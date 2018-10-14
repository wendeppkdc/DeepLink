# Match Deepbank files with Semlink

from utils.GraphUtils import deep_grapher
from utils.GraphUtils import graph_painter
from utils.VerbChecker import verb_checker
from utils.ArgMatcher import argmapper
import re
from loaders.PMLoader import PMLoader as pm

def DB_SL_matcher(deepbank, semlink, wsj, paint_mode=False):
    print("===================Start Deepbank-Semlink Matching===================")
    count = 0
    fullsent = 0
    vc = verb_checker("vb", True)
    type_error_adj = 0  # count adj-form verbs
    type_error_n = 0
    type_error_u = 0
    total_arg = 0
    miss_arg = 0
    none_type_error = 0
    wh_type_error = 0
    md_ng_type_error = 0  # will,etc md word in ARGM-MOD is obmitted in Deepbank

    for sent in semlink.keys():
        if sent in deepbank.keys():
            allsafe = True
            count += 1
            head, nodes, start_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"])
            for verb in semlink[sent]:
                if int(verb["token"]) in start_list.keys():
                    db_type = None
                    for node in start_list[int(verb["token"])]:
                        if node.cls.find("_v_") != -1:
                            db_type = node.cls
                            verb_node = node
                            verb_node.cls += "-" + pm.getFrame(verb["PB"])
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
                    if description == "rel":
                        continue

                    pointers = re.split("[;\*]", pointers)
                    for pointer in pointers:
                        starter, backcount = re.match(r"(\d*):(\d*)", pointer).groups()
                        ptb_node = wsj["t" + sent][int(starter)]

                        # TODO: deal with -NONE- token
                        if ptb_node.pos == "-NONE-":
                            none_type_error += 1
                            continue

                        for i in range(int(backcount)):
                            ptb_node = ptb_node.father
                        start, end = ptb_node.span

                        # TODO: deal with WHNP token
                        if ptb_node.pos[:2] == "WH":
                            wh_type_error += 1
                            continue

                        if description.find("=") >= 0:
                            description = description[0:description.find("=")]

                        argsafe = False
                        for edge in verb_node.succ:
                            if edge[1].addr[0] >= start and edge[1].addr[1] <= end:
                                argsafe = edge[0]
                                if paint_mode:
                                    edge[0] += "-" + pm.getFE(verb["PB"], description)

                        for edge in verb_node.prev:
                            if edge[1].addr[0] >= start and edge[1].addr[1] <= end:
                                argsafe = edge[1].cls+"."+edge[0]
                                if paint_mode:
                                    for edge0 in edge[1].succ:
                                        if edge0[1] == verb_node:
                                            edge0[0] += "-" + pm.getFE(verb["PB"], description)

                        total_arg += 1
                        if argsafe == False:
                            miss_arg += 1

                            # TODO: ArgM-MOD or ARG_NERG need special check
                            if ptb_node.pos == "MD" or ptb_node.pos == "RB":
                                md_ng_type_error += 1
                                continue

                            # TODO: Test here
                            # print(sent, verb["verb"], description, ptb_node.pos, start, end)
                            # print([t[1].addr for t in verb_node.prev],"-->O\t","O-->",[t[1].addr for t in verb_node.succ])
                            allsafe = False
                        else:
                            if not paint_mode:
                                argmapper.record(description, verb, db_type, argsafe, sent)

            # paint graph
            if paint_mode:
                nodes_painter = []
                edges_painter = []
                for handle in nodes.keys():
                    node = nodes[handle]
                    if node.name is None:
                        nodes_painter.append((handle, node.cls))
                    else:
                        nodes_painter.append((handle, node.cls + "(" + node.name + ")"))
                    for edge in node.succ:
                        edges_painter.append((edge[0], handle, edge[1].handle))
                graph_painter(sent, deepbank[sent]["src"], nodes_painter, edges_painter)

            if allsafe:
                fullsent += 1

    if not paint_mode:
        argmapper.write(".\\arg_matcher")
        #argmapper.show(deepbank)
        #argmapper.read(".\\test")

    print("{} / {} / {} verbs in Semlink are considered as (adj. / n. / unknown.) in deepbank.".format(type_error_adj,
                                                                                                       type_error_n,
                                                                                                       type_error_u))
    print("{} sentences matched between Semlink and Deepbank.".format(count))
    print("{} sentences are completely matched.".format(fullsent))
    print("{} of {} arguments are matched.".format(total_arg - miss_arg, total_arg))
    print(
        "Errors Detected: NONE-type:{}, WH-type:{}, MD/RB-type:{}".format(none_type_error, wh_type_error, md_ng_type_error))
    vc.show()
