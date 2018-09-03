import os
import os.path
import re
from loaders.DeepLoader import deep_loader
from loaders.SemLoader import sem_loader
from loaders.PTBLoader import ptb_loader
from utils.GraphUtils import deep_grapher
from utils.VerbChecker import verb_checker
from loaders.ONCompleter import on_comleter

# (document_id) (sentence number) (token number) (standard) (verb-v) (VerbNet class)
#  (Framenet Frame) (PB grouping) (SI grouping) (tense/aspect/mood info)
#  (ArgPointer)-ARGX=(VN Role);(FN Role/Optional Extra Fn Roles)
sem_parser = ["doc", "sent", "token", "stand", "verb", "verbnet", "frame", "PB", "SI", "TAM", "args"]

# nodes is a list of node, node is list of
# [hanlde, class, startpoint(token ord), endpoint(token ord, not include), extra information] (all elements are strings)
deepbank_parser = ["doc", "sent", "src", "nodes", "head"]

def traverse_dir(path, operator):
    sentenceSet = {}
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            sentenceSet.update(traverse_dir(child, operator))
        else:
            sentenceSet.update(operator.load(child))
    return sentenceSet

#  sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]
#  deepbank_parser=["doc","sent","src","nodes","head"]

if __name__ == "__main__":
    print("========================Start Basic Checking=========================")
    wsj=traverse_dir(".\\data\\wsj\\00", ptb_loader)
    on_comleter(wsj, ".\\data\\ptb3") # Fix on5.0 missing files with ptb files
    deep_loader.set_src(wsj)
    semlink = traverse_dir(".\\data\\semlink\\00", sem_loader)
    deepbank = traverse_dir(".\\data\\deepbank\\wsj00", deep_loader)
    print("Basic Checking Complete.")
    print()

    print("===================Start Deepbank-Semlink Matching===================")
    count = 0
    fullsent = 0
    total_verb = 0
    vc = verb_checker("vb", True)
    type_error_adj=0 #count adj-form verbs
    type_error_n=0
    type_error_u=0

    for sent in semlink.keys():
        if sent in deepbank.keys():
            count += 1
            head, nodes, start_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"])
            allsafe = True
            for verb in semlink[sent]:
                if int(verb["token"]) in start_list.keys():
                    db_type = None
                    for node in start_list[int(verb["token"])]:
                        if node.cls.find("_v_") != -1:
                            db_type = node.cls
                            break
                        elif node.cls.find("_a_") != -1:
                            type_error_adj+=1
                            break
                        elif node.cls.find("_n_") != -1:
                            type_error_n+=1
                            break
                        elif node.cls.find("_u_") != -1:
                            type_error_u+=1
                            break

                    if db_type is None:
                        continue

                    vc.check(db_type, verb)


                '''for arg in verb["args"]:
                    pointers, description = re.match(r"(.*?)-(.*)", arg).groups()

                    pointers = re.split("[;\*]", pointers)
                    for pointer in pointers:
                        start, end = re.match(r"(\d*):(\d*)", pointer).groups()
                        start = int(start)
                        end = int(end)
                        if start not in start_list.keys():
                            allsafe = False'''


    print("Semlink size: {}, Deepbank size: {}".format(len(semlink), len(deepbank)))
    print("{} of {} verbs in all Semlink lacked FN link, in {} sentences totally.".format(sem_loader.framemiss,
                                                                                          sem_loader.total_verb,
                                                                                          sem_loader.framemiss_sentence))
    print("{} / {} / {} verbs in Semlink are considered as (adj. / n. / unknown.) in deepbank.".format(type_error_adj, type_error_n,type_error_u))
    print("{} sentences matched between Semlink and Deepbank.".format(count))
    print("{} sentences are completely matched.".format(fullsent))
    vc.show()
