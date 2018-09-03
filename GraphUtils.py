#This module creates graph from a text model.
import re

sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]
deepbank_parser=["doc","sent","src","head","nodes"]

class Node:
    def __init__(self,handle,cls,addr,*,name=None,attr=None):
        self.handle=handle
        self.cls=cls
        self.addr=addr  #typeof tuple
        self.attr=attr
        self.name=name
        self.prev=[] # (edge type, previous points)
        self.succ=[] # (edge type, succeeding points)

    def setName(self,name):
        self.name=name

    def setAttr(self,attr):
        self.attr=attr

    def addPrev(self,startpoint):
        self.prev.append(startpoint)

    def addSucc(self,endpoint):
        self.succ.append(endpoint)

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
def deep_grapher(nodes_text, h, flagon=False):
    checklist=[]
    nodes={}
    edges={}
    start_list={}

    for node_text in nodes_text:
        handle, cls, start, end, extra=node_text
        node=Node(handle,cls,(start,end))

        if start not in start_list.keys():
            start_list[start]=[]
        start_list[start].append(node)

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

    return head, nodes, start_list