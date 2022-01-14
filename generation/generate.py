import re
import sys
import random

### Establishing grammar files
# Either assign command line parameters as grammar files,
# Or receive them from input
if len(sys.argv) == 1:
    original_grammar_name = input("Please provide the original grammar file: ")
    if original_grammar_name[-4:] != ".txt":
        raise ValueError("Please provide only text files as parameters.")

    target_grammar_name = input("Please provide the target grammar file: ")
    if target_grammar_name[-4:] != ".txt":
        raise ValueError("Please provide only text files as parameters.") 
elif len(sys.argv) == 3:
    original_grammar_name = sys.argv[1]
    target_grammar_name = sys.argv[2]

    if original_grammar_name[-4:] != ".txt":
        raise ValueError("Please provide only text files as parameters.")

    if target_grammar_name[-4:] != ".txt":
        raise ValueError("Please provide only text files as parameters.")
else:
    raise ValueError("Please provide zero parameters or two (original and target grammar files).")

### Extracting input types
original_grammar = open(original_grammar_name, 'r')
original_grammar_lines = original_grammar.readlines()

input_pattern = re.compile(r"input.*\[\d+\]:.*\"(.*)\"")

input_types = []

for l in original_grammar_lines:
    match_list = re.findall(input_pattern, l)
    if len(match_list) > 1:
        raise ValueError("Multiple inputs found for one tableau. Please check grammar file.")
    
    for match in match_list:
        input_types.append(match)

iteration = int(input("How many iterations per input type? "))

input_tokens = []

for inp in input_types:
    counter = 0
    while counter < iteration:
        input_tokens.append(inp)
        counter += 1
random.shuffle(input_tokens)

### Extracting ranking values
target_grammar = open(target_grammar_name, 'r')
target_grammar_string = target_grammar.read()

const_pattern = re.compile(r"\"(.*)\"\t([\d\.]+)")
const_rv = re.findall(const_pattern, target_grammar_string)
const_rv = [(x[0], float(x[1])) for x in const_rv]

ranked_tuples = sorted(const_rv, key = lambda x:x[1], reverse=True)
ranked_consts = [x[0] for x in ranked_tuples]

### Define the optimizing functions
def optimize(tableau_viol_only):
    # Pick out the most serious offense of each parse
    # (I.e., pick out the highest-ranked constraint violated by the parse)
    initial_batch = []
    for value in tableau_viol_only.values():
        # The value is a list of (parse, const_rank, const, viol) tuples, sorted by const_rank.
        # The first element of this list is the "most serious offense."
        initial_batch.append(value[0])

    # Among the most serious offense commited by each parse, 
    # pick out the parse(s) that committed the least serious one.
    lowest_rank_compare = []
    # max, because the *largest* const_rank value means least serious
    lowest_rank = max(initial_batch, key = lambda x:x[1])
    for parse in initial_batch:
        if parse[1] == lowest_rank[1]:
            lowest_rank_compare.append(parse)

    # If there is a single parse with the least serious offense, that's the winner.
    if len(lowest_rank_compare) == 1:
        return lowest_rank_compare[0]

    # If there are more than one least-serious offenders...
    elif len(lowest_rank_compare) > 1:
        # ... we first see whether one has violated the same constraint more than the other(s).
        viol_compare = []
        lowest_viol = min(lowest_rank_compare, key = lambda x:x[3])
        for x in lowest_rank_compare:
            if x[3] == lowest_viol[3]:
                viol_compare.append(x)

        # If there is one parse that violated the constraint the least, that's the winner.
        if len(viol_compare) == 1:
            return viol_compare[0]
        
        # If all of the least-serious offenders violated the constraint the same number of times,
        # we now need to compare their next most serious constraint offended.
        elif len(viol_compare) > 1:
            partial_tableau_viol_only = {}
            for x in viol_compare:
                # Make another tableau_viol_only with the least-serious offenders,
                # but we chuck out their most serious offenses.
                partial_tableau_viol_only[x[0]] = tableau_viol_only[x[0]][1:]
            # Run the algorithm again with the new, partial tableau_viol_only
            return optimize(partial_tableau_viol_only)
        else:
            raise ValueError("Could not find optimal candidate")
    else:
        raise ValueError("Could not find optimal candidate")

# Produce a winning parse given an input and constraint ranking
# (Basically a run-of-the-mill OT tableau)
def generate(inp, ranked_consts):
    # Pick out the constraints that *are* violated (i.e., violation > 0)
    # This "sub-dictionary" will be fed into the optimize function
    tableau_viol_only = {}
    for parse in input_tokens:
        tableau_viol_only[parse] = []
        for const, viol in input_tableaux[inp][parse].items():
            if viol > 0:
                tableau_viol_only[parse].append((parse, ranked_consts.index(const), const, viol))
        tableau_viol_only[parse] = sorted(tableau_viol_only[parse], key = lambda x:x[1])

    gen_parse = optimize(tableau_viol_only)[0]
    
    return gen_parse

for token in input_tokens:
    print(generate(token, ranked_consts))
