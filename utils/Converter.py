from utils.GraphUtils import deep_grapher
from utils.GraphUtils import graph_painter
from utils.ArgMatcher import argmapper
import re
from loaders.PMLoader import PMLoader as pm


def DB_PM_converter(deepbank):
    print("===================Start Deepbank-Predicate Matrix Matching===================")
    argmapper.read(".\\arg_matcher")
    for sent in deepbank.keys():
        head, nodes, start_list, verb_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"],
                                                          require_verb=True)
        reserve = False
        for node in verb_list:
            if node.cls.find("_v_") != -1:
                if argmapper.getPBG(node.cls):
                    if re.match("fn.", pm.getFrame(argmapper.getPBG(node.cls))):
                        reserve = True
                        pbg = argmapper.getPBG(node.cls)
                        for edge in node.succ:
                            pbr = argmapper.getPBR(node.cls + "-" + edge[0])
                            if pbr:
                                if re.match("fn.", pm.getFE(pbg, pbr)):
                                    edge[0] = pm.getFE(pbg, pbr)
                        node.cls += "-" + pm.getFrame(pbg)

        if reserve:
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
