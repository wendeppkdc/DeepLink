# This Procedure is used for extracting tokens from ptb file (PTB3 style or ON5.0 style)

from loaders.SpecialCases import special_transform
from loaders.AddZeros import addZeros
from utils.TreeUtils import Node
import re


class ptb_loader:
    token_pattern = re.compile(r"[ \(]]")

    def load(path):
        ptb = open(path, "r")
        doc = re.search(r"\\wsj_(\d*)\.", path).groups()[0]
        index = -1
        sentence_set = {}
        stack = []

        for line in ptb:
            if line[0] == "(":
                if index != -1:
                    sentence_set[doc + addZeros(index)] = sent
                    sentence_set["t" + doc + addZeros(index)] = tsent
                sent = []
                tsent = []
                index += 1

            line = line.lstrip()[:-1]
            loc = 0

            while loc < len(line):
                if line[loc] == "(":
                    space = line.find(" ", loc + 1)
                    pos = line[loc + 1:space]
                    stack.append(Node(pos))
                    loc = space + 1
                elif line[loc] == ")":
                    last = stack.pop()
                    if len(stack) > 0:
                        stack[-1].setChild(last)
                        last.setFather(stack[-1])
                    loc += 1
                elif line[loc] == " ":
                    loc += 1
                else:
                    next = line.find(")", loc + 1)
                    token = line[loc:next]
                    stack[-1].setToken(token)
                    loc = next

                    # special cases
                    pos, token = special_transform(pos, token)
                    sent.append([pos, token])
                    tsent.append(stack[-1])

        sentence_set[doc + addZeros(index)] = sent
        sentence_set["t" + doc + addZeros(index)] = tsent
        return sentence_set
