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

grammar_file = open(sys.argv[1], 'r')
grammar_text = grammar_file.read()

### Extract list of constraints, preserving order in grammar file
constraint_pattern = re.compile(r"constraint\s+\[\d+\]:\s(\".*\").*")
constraints = re.findall(constraint_pattern, grammar_text)

const_dict={}
for c in constraints:
    const_dict[c] = 100

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

# Extract violation profile for each candidate for each input
'''
Sample structure of a tableau:

{"[L1 H]": {"/(L1) H/": (("WSP", 1), ("Iambic", 0), ...),
            "/(L1 H)/": (("WSP", 0), ("Iambic", 1), ...),
           ...}
 "[L1 L]": {"/(L1) L/": (("WSP", 0), ("Iambic", 0), ...),
           ...}
 ...}

'''    
tableaux = {}
for t in tableaux_string:
    # Pick out the input (e.g., "|L L|") from tableau
    input_pattern = re.compile(r"input\s\[\d+\]:\s(\".*\")")
    inp = re.findall(input_pattern, t)[0] # re.findall will always return list of len 1

    # Pick out the candidates (e.g., "[L1 L] -> /(L1) L/") and their violation profile
    candidate_pattern = re.compile(r"candidate.*(\".*\")\s([\d|\s]+)")
    
    # dictionary will be {<candidate 1>: <violation_profile>, <candidate 2>: <violation_profile>, ...}
    optimizations = {}

    # re.findall returns tuples of (<candidate>, <violation profile>)
    # length of list returned by re.findall will equal number of candidates
    for tup in re.findall(candidate_pattern, t):
        candidate, viols_raw = tup

        # convert violation profile (e.g., '0 1 0') from string to list (e.g., ['0', '1', '0'])
        viols = viols_raw.rstrip().split(' ')
        viols = [int(x) for x in viols] # convert string to integer

        # Map the list of constraints with list of violations,
        # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
        const_viols = map_lists_to_tuple_list(constraints, viols)

        optimizations[candidate] = const_viols
    
    tableaux[inp] = optimizations

# Close files
grammar_file.close()


##### Part 2: Defining utility functions #######################################

def random_noise(const_dict):
    for constraint in const_dict:
        noise = random.uniform(-2.0, 2.0)
        const_dict[constraint] = const_dict[constraint]+noise
    return const_dict

def ranking(dict):
    ranked_list_raw=[]
    for constraint in dict:
        ranked_list_raw.append((constraint, dict[constraint]))
    ranked_list_raw = sorted(ranked_list_raw, key=lambda item: item[1], reverse=True)
    ranked_list = [x[0] for x in ranked_list_raw]
    return ranked_list

def get_highest_violation(viols_tuple, ranked_constraints):
    for viol in viols_tuple:
        if viol[0] not in ranked_constraints:
            print(viol+" is not a valid constraint")
            exit
    viols_tuple_copy = viols_tuple
    viols_tuple_copy = sorted(viols_tuple_copy, key=lambda x: ranked_constraints.index(x[0]))
    for viol in viols_tuple_copy:
        if viol[1] == 1:
            return viol[0]
            exit
    return None

def get_all_violations(viols_tuple, ranked_constraints):
    violations = []
    for viol in viols_tuple:
        if viol[0] not in ranked_constraints:
            print(viol+" is not a valid constraint")
            exit
    viols_tuple_copy = viols_tuple
    viols_tuple_copy = sorted(viols_tuple_copy, key=lambda x: ranked_constraints.index(x[0]))
    for viol in viols_tuple_copy:
        if viol[1] == 1:
            violations.append(viol)
    if len(violations) > 0:
        return violations
    else:
        return None

def optimize(inp, ranked_constraints):
    candidates = []
    for cand, value in tableaux[inp].items():
        candidates.append((cand, get_highest_violation(tableaux[inp][cand], ranked_constraints)))
    candidates = sorted(candidates, key=lambda x:ranked_constraints.index(x[1]), reverse=True)
    return(candidates[0][0])

def detect_error()



ranked_constraints = ranking(random_noise(const_dict))

print(optimize('"|L H|"', ranked_constraints))



