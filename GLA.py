
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
import math

#lang = sys.argv[1][:6]
#syll_num = sys.argv[1][-9]

##### Part 0: Open and save grammar and target files ############################



# The Grammar file is a specific format of a txt file created by Praat
# (It is called an "otgrammar" object in the Praat documentation.

def grammar_string(txtfile):
    grammar_file = open(txtfile, 'r')
    grammar_text = grammar_file.read()
    grammar_file.close()
    return grammar_text

def grammar_readlines(txtfile):
    grammar_file = open(txtfile, 'r')
    grammar_lines = grammar_file.readlines()
    grammar_file.close()
    return grammar_lines

def target_readlines(txtfile):
    target_file = open(txtfile, 'r')
    target_list = target_file.readlines()
    target_list = [x.rstrip() for x in target_list]
    target_file.close()
    return target_list

##### Part 1: Extract Information from Grammar File ############################

# Praat's otgrammar file is a list of constraints followed by a list of OT tableaux, 
# which provide information about the violation profile for each input-parse pair. 
# The format of a tableaux and its elements (input form, overt form, violation profile) 
# can be expressed in regular grammar.

### Extract list of constraints, preserving their order in grammar file
# Preserving order is important because the violation profiles in the tableaux 
# are based on this order.

### Regex Patterns
const_pattern = re.compile(r"constraint\s+\[\d+\]:\s(\".*\")\s*([\d\.]+)\s*")
tableau_pattern = re.compile(r"(input.*\n(\s*candidate.*\s*)+)")
input_pattern = re.compile(r"input\s+\[\d+\]:\s+\"(.*)\"") 
candidate_pattern = re.compile(r"candidate.*\[\d+\]:.*\"(.*)\"\D*([\d ]+)")
rip_pattern = re.compile(r"(\[.*\]).*(/.*/)")


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
    if len(listone) != len(listtwo):
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
          ...
          }
 input2: {overt1: {parse1: violation profile
                   parse2: violation profile}
          overt2: {parse1: violation profile
                   parse2: violation profile
                   parse3: violation profile
                   parse4: violation profile}
          ...
          } 
 input3: ...
}
'''    

### There will be two separate dictionaries: 
### one where parses are aggregated by input (input_tableaux),
### and one where parses are aggregated by overt form (overt_tableaux).

### Now we can build the two tableaux.
# Build input_tableaux -- code very similar to overt_tableaux
def build_input_tableaux(grammar_string):
    tableaux_string = re.findall(tableau_pattern, grammar_string)
    tableaux_string = [t[0] for t in tableaux_string]
    consts = re.findall(const_pattern, grammar_string)
    
    input_tableaux = {}
    for t in tableaux_string:
        # Since there's only one input form per tableau,
        # re.findall should always yield a list of length 1)
        if len(re.findall(input_pattern, t)) == 0:
            raise ValueError("No input found in the following tableaux_string. Pleae check grammar file.\n"+t)
        elif len(re.findall(input_pattern, t)) > 1:
            raise ValueError("Found more than one input form in tableau. Please check grammar file.")

        inp = re.findall(input_pattern, t)[0]

        # Access the candidates again, to pick out parse and violation profile.
        # Each element of canddiates is a (<candidate>, <violation profile>) tuple.
        candidates = re.findall(candidate_pattern, t)
        
        # Following for-loop is identical to overt_tableaux
        parse_evals = {}
        for cand in candidates:
            parse = cand[0]
            viols_string = cand[1]
            viols = viols_string.rstrip().split(' ')
            viols = [int(x) for x in viols] 

            viol_profile = map_lists_to_dict(consts, viols)
            parse_evals[parse] = viol_profile
            
        input_tableaux[inp] = parse_evals
    
    return input_tableaux

def build_input_tableaux_RIP(grammar_string):
    tableaux_string = re.findall(tableau_pattern, grammar_string)
    tableaux_string = [t[0] for t in tableaux_string]
    consts = re.findall(const_pattern, grammar_string)
    
    input_tableaux = {}
    for t in tableaux_string:
        # Since there's only one input form per tableau,
        # re.findall should always yield a list of length 1)
        if len(re.findall(input_pattern, t)) == 0:
            raise ValueError("No input found in the following tableaux_string. Pleae check grammar file.\n"+t)
        elif len(re.findall(input_pattern, t)) > 1:
            raise ValueError("Found more than one input form in tableau. Please check grammar file.")

        inp = re.findall(input_pattern, t)[0]

        # Access the candidates again, to pick out parse and violation profile.
        # Each element of candidates is a (<candidate>, <violation profile>) tuple.
        candidates = re.findall(candidate_pattern, t)
        
        # Following for-loop is identical to overt_tableaux
        parse_evals = {}
        for cand in candidates:
            # The candidate string for an RIP includes both the parse and the output.
            # I.e., "/output/ \-> [parse]"
            parse_and_output = cand[0]
            if len(re.findall(rip_pattern, parse_and_output)) != 1:
                raise ValueError("Candidate "+cand+" doesn't look like an RIP candidate. Please check grammar file.")
            output = re.findall(rip_pattern, parse_and_output)[0]
            parse = re.findall(rip_pattern, parse_and_output)[1]
            viols_string = cand[1]

            viols = viols_string.rstrip().split(' ')
            viols = [int(x) for x in viols] 

            viol_profile = map_lists_to_dict(consts, viols)
            parse_evals[parse] = viol_profile
            
        input_tableaux[inp] = parse_evals
    
    return input_tableaux

def build_overt_tableaux_RIP(grammar_string):
    tableaux_string = re.findall(tableau_pattern, grammar_string)
    tableaux_string = [t[0] for t in tableaux_string]
    consts = re.findall(const_pattern, grammar_string)

    overt_tableaux = {}
    for t in tableaux_string:
        candidates_match = re.findall(candidate_pattern, t)

        overt_set = []
        candidates = []
        # candidates 
        for match in candidates_match:
            parse_and_overt = match[0]
            if len(re.findall(rip_pattern, parse_and_overt)) != 1:
                raise ValueError("Candidate "+parse_and_overt+" doesn't look like an RIP candidate. Please check grammar file.")
            overt = re.findall(rip_pattern, parse_and_overt)[0][0]
            parse = re.findall(rip_pattern, parse_and_overt)[0][1]
            viol_string = match[1]

            overt_set.append(overt)
            candidates.append((overt, parse, viol_string))
        overt_set = set(overt_set)

        for overt in overt_set:
            parse_evals = {}

            for cand in candidates:
                cand_overt = cand[0]
                cand_parse = cand[1]
                cand_viol_string = cand[2]

                if overt == cand_overt:
                    # convert violation profile from string to list
                    # E.g., from '0 1 0' to ['0', '1', '0']
                    viols = cand_viol_string.rstrip().split(' ')
                    # convert string (e.g., '0') to integer (e.g., 0)
                    viols = [int(x) for x in viols]
                    # Map the list of constraints with list of violations,
                    # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
                    viol_profile = map_lists_to_dict(consts, viols)

                    parse_evals[cand_parse] = viol_profile
            
            overt_tableaux[overt] = parse_evals
    
    return overt_tableaux

string = grammar_string('./grammars/hypo02_grammar.txt')

print(build_overt_tableaux_RIP(string).keys())



exit()

'''
# Only RIP needs to build overt tableaux
def build_overt_tableaux_RIP(grammar_string):
    tableaux_string = re.findall(tableau_pattern, grammar_string)
    tableaux_string = [t[0] for t in tableaux_string]
    consts = re.findall(const_pattern, grammar_string)
    
    overt_tableaux = {}
    for t in tableaux_string:
        # Since the parentheses in the candidate_pattern regex capture these three string groups,
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
                    # convert violation profile from string to list
                    # E.g., from '0 1 0' to ['0', '1', '0']
                    viols = viols_string.rstrip().split(' ')
                    # convert string (e.g., '0') to integer (e.g., 0)
                    viols = [int(x) for x in viols] 

                    # Map the list of constraints with list of violations,
                    # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
                    viol_profile = map_lists_to_dict(consts, viols)
                    
                    parse_evals[parse] = viol_profile

            overt_tableaux[overt] = parse_evals

    return overt_tableaux
'''

##### Part 2: Defining utility functions #######################################
# Make constraint dictionary
def const_dict(grammar_string, initiate=False, init_value=100.0):
    const_dict = {}
    consts_rv = re.findall(const_pattern, grammar_string)
    if initiate:
        for const in consts_rv:
            const_dict[str(const[0])] = float(init_value)
    else:
        for const in consts_rv:
            const_dict[str(const[0])] = float(const[1])
    return const_dict

def find_input(overt_string, input_tableaux):
    potential_inps = []
    for inp in input_tableaux.keys():
        if overt_string in input_tableaux[inp].keys():
            potential_inps.append(inp)
    if len(potential_inps) == 0:
        raise ValueError("No input found: "+overt_string+" is not a candidate in this grammar file.")
    return potential_inps

# Output is not 'found' from the tableaux in RIP-GLA.
# In fact, the whole point of doing RIP is to find the right input.
# E.g., is [H1 H2] analyzed as /(H1 H2)/ or /(H1) (H2)/?
def make_input(overt_string):
    core_pattern = re.compile(r"\[(.*)\]")
    if not re.search(core_pattern, overt_string):
        raise ValueError("Format of overt form "+overt_string+" is not appropriate. It should look like '[L1 H H]'.")

    core = re.search(core_pattern, overt_string).group(1)
    core = re.sub(r"\d", "", core)
    inp = "|"+core+"|"
    return inp
# Add random noise to ranking values of each constraint
def add_noise(const_dict, noise_sigma=2.0):
    const_dict_copy = const_dict.copy()
    for const in const_dict.keys():
        noise = random.gauss(0, noise_sigma)
        const_dict_copy[const] = const_dict[const] + noise
    return const_dict_copy

# Rank constraints in const_dict by their ranking value and return an ordered list
def ranking(const_dict):
    ranked_list_raw=[]
    for const in const_dict:
        ranked_list_raw.append((const, const_dict[const]))
    # Random shuffle raw list to get rid of the effects of Python's default ordering
    random.shuffle(ranked_list_raw) 
    ranked_list_raw = sorted(ranked_list_raw, key=lambda x: x[1], reverse=True)
    ranked_list = [x[0] for x in ranked_list_raw]
    return ranked_list

# A recursive function that does run-of-the-mill OT
# It takes as argument a special dictionary, tableau_viol_only, which acts as a sub-tableau of sorts.
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
def generate(inp, ranked_consts, input_tableaux):
    # Pick out the constraints that *are* violated (i.e., violation > 0)
    # This "sub-dictionary" will be fed into the optimize function
    tableau_viol_only = {}
    for parse in input_tableaux[inp].keys():
        tableau_viol_only[parse] = []
        for const, viol in input_tableaux[inp][parse].items():
            if viol > 0:
                tableau_viol_only[parse].append((parse, ranked_consts.index(const), const, viol))
        tableau_viol_only[parse] = sorted(tableau_viol_only[parse], key = lambda x:x[1])

    gen_parse = optimize(tableau_viol_only)[0]
    gen_viol_profile = input_tableaux[inp][gen_parse]
    
    return (gen_parse, gen_viol_profile)
        
# Produce a winning parse given an overt form and constraint ranking
# Very similar to generate, except that the candidates are not inputs but overts
def rip(overt, ranked_consts, overt_tableaux):
    tableau_viol_only = {}
    for parse in overt_tableaux[overt].keys():
        tableau_viol_only[parse] = []
        for const, viol in overt_tableaux[overt][parse].items():
            if viol > 0:
                tableau_viol_only[parse].append((parse, ranked_consts.index(const), const, viol))
        tableau_viol_only[parse] = sorted(tableau_viol_only[parse], key = lambda x:x[1])
    
    rip_parse = optimize(tableau_viol_only)[0]
    rip_viol_profile = overt_tableaux[overt][rip_parse]
    
    return (rip_parse, rip_viol_profile)

# Adjusting the grammar, given the list of good and bad constraints
def adjust_grammar(good_consts, bad_consts, const_dict, plasticity=1.0):
    for const in good_consts:
        const_dict[const] = const_dict[const] + float(plasticity)
    for const in bad_consts:
        const_dict[const] = const_dict[const] - float(plasticity)
    return const_dict

# In the face of an error, classify constraints into good, bad, and irrelevant constraints.
def learn(winner_viol_profile, loser_viol_profile, const_dict, plasticity):
    good_consts = [] # Ones that are violated more by the "wrong" parse than by the actual datum
    bad_consts = [] # Ones that are violated more by actual datum than by the "wrong" parse
    for const in winner_viol_profile.keys():
        if winner_viol_profile[const] > loser_viol_profile[const]:
            bad_consts.append(const)
        elif winner_viol_profile[const] < loser_viol_profile[const]:
            good_consts.append(const)
        else: # equal number of violations for the parse and the datum
            continue
    # Adjust the grammar according to the contraint classifications
    return adjust_grammar(good_consts, bad_consts, const_dict, plasticity)

def do_learning_RIP(target_list, const_dict, input_tableaux, overt_tableaux, plasticity=1.0, noise_bool=True, noise_sigma=2.0):
    target_list_shuffled = random.sample(target_list, len(target_list))

    for t in target_list_shuffled:
        if noise_bool==True:
            const_dict_noisy = add_noise(const_dict, noise_sigma)
            generation = generate(make_input(t), ranking(const_dict_noisy), input_tableaux)
            rip_parse = rip(t, ranking(const_dict_noisy), overt_tableaux)
        else:
            generation = generate(make_input(t), ranking(const_dict), input_tableaux)
            rip_parse = rip(t, ranking(const_dict), overt_tableaux)

        if generation[0] == rip_parse[0]:
            continue
        else:
            # new grammar
            const_dict = learn(rip_parse[1], generation[1], const_dict, plasticity)
            # new generation with new grammar
            generation = generate(make_input(t), ranking(const_dict), input_tableaux)
            # new rip parse with new grammar
            rip_parse = rip(t, ranking(const_dict), overt_tableaux)
    
    return const_dict

def do_learning(target_list, const_dict, input_tableaux, plasticity=1.0, noise_bool=True, noise_sigma=2.0):
    target_list_shuffled = random.sample(target_list, len(target_list))

    for t in target_list_shuffled:
        inp = find_input(t, input_tableaux)
        if noise_bool==True:    
            generation = generate(inp, ranking(add_noise(const_dict, noise_sigma)), input_tableaux)
        else:
            generation = generate(inp, ranking(const_dict), input_tableaux)

        if generation[0] == t:
            continue
        else:
            # new grammar
            constraint_dict = learn(input_tableaux[inp][t], generation[1], constraint_dict, plasticity)
            # new generation with new grammar
            generation = generate(inp, ranking(constraint_dict), input_tableaux)
    
    return const_dict

#tgts = target_readlines('ilokano_toydata.txt')
#cd = const_dict(grammar_string('ilokano_grammar.txt'), True, 100)

#print(do_learning(tgts, cd, inpt))


'''


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
interval_track = [] 
# track number of learned tokens
learning_track = []
# track number of iterations for plotting
iteration_track = []

datum_counter = 0
change_counter = 0

# Actual learning loop

for t in target_list_shuffled:
    datum_counter += 1

    if noise:
        constraint_dict_noisy = add_noise(constraint_dict)
        generation = generate(get_input(t), ranking(constraint_dict_noisy))
        rip_parse = rip(t, ranking(constraint_dict_noisy))
    else:
        generation = generate(get_input(t), ranking(constraint_dict))
        rip_parse = rip(t, ranking(constraint_dict))


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

        interval_track.append(datum_counter)

        for const in constraint_dict.keys():
            trend_tracks[const].append(constraint_dict[const])
    
    iteration_track.append(datum_counter)
    learning_track.append(len(learned_success_list))

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
intervals = []
changes = []
for i in range(0, len(interval_track)-1):
    intervals.append(interval_track[i+1]-interval_track[i])
    changes.append(i+1)

plt.subplot(3, 1, 1)  
for const in constraint_dict.keys():
    plt.plot(iteration_track, trend_tracks[const], label=str(const))
    #plt.xscale('log')

#labelLines(plt.gca().get_lines(), align=False, fontsize=12)

i = 0
yticks_learning = []
while i < len(learned_success_list):
    if math.floor(len(learned_success_list)*0.25) == float(i):
        yticks_learning.append(i)
    elif math.floor(len(learned_success_list)*0.5) == float(i):
        yticks_learning.append(i)
    elif math.floor(len(learned_success_list)*0.75) == float(i):
        yticks_learning.append(i)
    else:
        pass

    i += 1

yticks_learning.append(len(learned_success_list))

plt.subplot(3, 1, 2)
plt.plot(iteration_track, learning_track)
#plt.xscale('log')
plt.yticks(yticks_learning)
# y-axis for learning track should be 1, 2, ..., num_of_datum_tokens



plt.subplot(3, 1, 3)
plt.plot(changes, intervals)
plt.ylim(0, max(intervals)+1)
#yticks_intervals = list(range(max(intervals)+1))
#plt.yticks(yticks_intervals)


fig_path = result_file_path[:-4]+".pdf"
plt.savefig(fig_path)
plt.show()
'''