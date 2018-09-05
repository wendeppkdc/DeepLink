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
    wsj = traverse_dir(".\\data\\wsj\\00", ptb_loader)
    on_comleter(wsj, ".\\data\\ptb3")  # Fix on5.0 missing files with ptb files
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
    type_error_adj = 0  # count adj-form verbs
    type_error_n = 0
    type_error_u = 0
    total_arg=0
    miss_arg=0
    none_type_error=0
    wh_type_error=0
    md_ng_type_error=0 #will,etc md word in ARGM-MOD is obmitted in Deepbank

    for sent in semlink.keys():
        if sent in deepbank.keys():
            allsafe=True
            count += 1
            head, nodes, start_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"])
            for verb in semlink[sent]:
                if int(verb["token"]) in start_list.keys():
                    db_type = None
                    for node in start_list[int(verb["token"])]:
                        if node.cls.find("_v_") != -1:
                            db_type = node.cls
                            verb_node = node
                            break
                        elif node.cls.find("_a_") != -1:
                            type_error_adj += 1
                            break
                        elif node.cls.find("_n_") != -1:
                            type_error_n += 1
                            break
                        elif node.cls.find("_u_") != -1:
                            type_error_u += 1
                            break

                    if db_type is None:
                        continue

                    vc.check(db_type, verb)

                for arg in verb["args"]:
                    pointers, description = re.match(r"(.*?)-(.*)", arg).groups()
                    if description=="rel":
                        continue

                    pointers = re.split("[;\*]", pointers)
                    for pointer in pointers:
                        starter, backcount = re.match(r"(\d*):(\d*)", pointer).groups()
                        ptb_node = wsj["t" + sent][int(starter)]

                        #TODO: deal with -NONE- token
                        if ptb_node.pos == "-NONE-":
                            none_type_error+=1
                            continue

                        for i in range(int(backcount)):
                            ptb_node = ptb_node.father
                        start, end = ptb_node.span

                        #TODO: deal with WHNP token
                        if ptb_node.pos[:2]=="WH":
                            wh_type_error+=1
                            continue

                        argsafe = False
                        for node in verb_node.succ:
                            if node[1].addr[0]>=start and node[1].addr[1] <= end:
                                argsafe = True

                        for node in verb_node.prev:
                            if node[1].addr[0] >= start and node[1].addr[1] <= end:
                                argsafe = True

                        total_arg+=1
                        if not argsafe:
                            #TODO: ArgM-MOD or ARG_NERG need special check
                            if ptb_node.pos=="MD" or ptb_node.pos=="RB":
                                md_ng_type_error+=1
                                continue

                            #TODO: Test here
                            print(sent, verb["verb"], description, ptb_node.pos, start, end)
                            print([t[1].addr for t in verb_node.prev],"-->O\t","O-->",[t[1].addr for t in verb_node.succ])
                            allsafe=False
                            miss_arg+=1

            if allsafe:
                fullsent += 1

    print("Semlink size: {}, Deepbank size: {}".format(len(semlink), len(deepbank)))
    print("{} of {} verbs in all Semlink lacked FN link, in {} sentences totally.".format(sem_loader.framemiss,
                                                                                          sem_loader.total_verb,
                                                                                          sem_loader.framemiss_sentence))
    print("{} / {} / {} verbs in Semlink are considered as (adj. / n. / unknown.) in deepbank.".format(type_error_adj,
                                                                                                       type_error_n,
                                                                                                       type_error_u))
    print("{} sentences matched between Semlink and Deepbank.".format(count))
    print("{} sentences are completely matched.".format(fullsent))
    print("{} of {} arguments are matched.".format(total_arg-miss_arg, total_arg))
    print("Errors Detected: NONE-type:{}, WH-type:{}, MD/RB-type:{}".format(none_type_error,wh_type_error,md_ng_type_error))
    vc.show()
