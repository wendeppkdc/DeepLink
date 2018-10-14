# This module creates graph from deepbank.
import re
from graphviz import Digraph
from graphviz import dot as dotx
import pydot


sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]
deepbank_parser=["doc","sent","src","head","nodes"]

class Node:
    def __init__(self,handle,cls,addr,*,name=None,attr=None):
        self.handle=handle
        self.cls=cls
        self.addr=list(addr)  #typeof tuple
        self.attr=attr
        self.name=name
        self.prev=[] # (edge type, previous points)
        self.succ=[] # (edge type, succeeding points)

    def setName(self,name):
        self.name=name

    def setAttr(self,attr):
        self.attr=attr

    def addPrev(self,startpoint):
        self.prev.append(list(startpoint))

    def addSucc(self,endpoint):
        self.succ.append(list(endpoint))

def isCon(head, checklist):
    if head in checklist:
        checklist.remove(head)
    else:
        return False
    if len(checklist)==0:
        return True
    for edge in head.prev:
        if isCon(edge[1],checklist):
            return True
    for edge in head.succ:
        if isCon(edge[1],checklist):
            return True
    return False

# "flagon" is a switch for Connectivity Checking
# "start_list" is used for map start-position to nodes
def deep_grapher(nodes_text, h, flagon=False, require_verb=False):
    checklist=[]
    nodes={}
    edges={}
    start_list={}
    verb_list=[]

    for node_text in nodes_text:
        handle, cls, start, end, extra=node_text
        node=Node(handle,cls,(start,end))

        if start not in start_list.keys():
            start_list[start]=[]
        start_list[start].append(node)
        if require_verb and node.cls.find("_v_"):
            verb_list.append(node)

        nodes[handle]=node
        if handle == h:
            head = node
        checklist.append(node)
        if extra.find("{")!=-1:
            node.setAttr(re.search(r"\{(.*)\}",extra).groups()[0])

        if extra.find("(")!=-1:
            node.setName(re.search(r"\((.*)\)",extra).groups()[0])

        if len(re.search(r"\[(.*)\]", extra).groups()[0])>0:
            edges[handle] = re.search(r"\[(.*)\]", extra).groups()[0].split(",")

    total=len(checklist)

    for startpoint in edges.keys():
        for edge in edges[startpoint]:
            type, endpoint=edge.strip().split(" ")
            nodes[startpoint].addSucc((type,nodes[endpoint]))
            nodes[endpoint].addPrev((type,nodes[startpoint]))

    if flagon and not isCon(head,checklist):
        print("Connectivity Warning, {} of {} nodes remained".format(len(checklist), total))

    if require_verb:
        return head, nodes, start_list, verb_list
    else:
        return head, nodes, start_list

def graph_painter(filename,raw, nodes,edges):
    outputdir = 'C:\\Users\\wendeppkdc\\Desktop\\visualization\\'
    dot=Digraph(comment=raw,format="png")

    filename = outputdir + filename
    for node in nodes:
        id = node[0]
        name = node[1]
        dot.node(id, name)
    for edge in edges:
        dot.edge(edge[1], edge[2], edge[0])

    dot.render(filename + ".gv")
