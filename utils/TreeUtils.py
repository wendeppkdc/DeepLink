# Util for PTB-style phrase structure tree

class Node:
    def __init__(self, pos):
        self.token = None
        self.pos = pos
        self.span = [pos, pos + 1]  # The span of tokens the node covers
        self.father = None  # (fathers)
        self.children = []  # (children)

    def setFather(self, father):
        self.father = father

    def setChild(self, child):
        self.children.append(child)
        self.span = [min(self.span[0], child.span[0]), max(self.span[1], child.span[1])]

    def setToken(self, token):
        self.token = token
