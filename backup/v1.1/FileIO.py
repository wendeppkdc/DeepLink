import os
import os.path
import gzip
import pdb
import re
from GraphUtils import *
import random
import pickle

# (document_id) (sentence number) (token number) (standard) (verb-v) (VerbNet class)
#  (Framenet Frame) (PB grouping) (SI grouping) (tense/aspect/mood info)
#  (ArgPointer)-ARGX=(VN Role);(FN Role/Optional Extra Fn Roles)
sem_parser = ["doc", "sent", "token", "stand", "verb", "verbnet", "frame", "PB", "SI", "TAM", "args"]

# nodes is a list of node, node is list of
# [hanlde, class, startpoint(token ord), endpoint(token ord, not include), extra information] (all elements are strings)
deepbank_parser = ["doc", "sent", "src", "nodes", "head"]

sembank = {}
deepbank = {}


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


def addZeros(num):
    s = str(int(num) + 1)
    return "0" * (3 - len(s)) + s


class sem_loader:
    framemiss = 0
    total_verb = 0
    framemiss_sentence = 0
    token_pattern = re.compile(r"\([^()]*\)")

    def load(path):
        sentence_set = {}
        with open(path, "r") as file:
            doc = re.search(r"\_(.*)\.", path).groups()[0]
            sent = "-1"
            verbs = None
            for line in file:
                sem_loader.total_verb += 1
                args = line.strip().split(" ")
                sentence = {}
                sentence["doc"] = doc
                for index in range(10):
                    sentence[sem_parser[index]] = args[index]
                args = args[10:]
                sentence["args"] = args
                if sent == "-1":
                    sent = sentence["sent"]
                    verbs = []
                    miss = False

                if sentence["frame"] in ["IN", "NF"]:
                    sem_loader.framemiss += 1
                    miss = True

                if sent != sentence["sent"]:
                    if miss:
                        sem_loader.framemiss_sentence += 1
                    sentence_set[doc + addZeros(sent)] = verbs
                    sent = sentence["sent"]
                    verbs = []
                    verbs.append(sentence)
                    miss = False
                else:
                    verbs.append(sentence)

            sentence_set[doc + addZeros(sent)] = verbs
            if miss:
                sem_loader.framemiss_sentence += 1

        return sentence_set


# deal with speical cases in PTB file
# transport label to real token
def special_transform(spt):
    if spt[1] == "``" or spt[1] == "''":
        spt[0] = spt[1] = "\""
    elif spt[1] == "-LRB-":
        spt[0] = spt[1] = "("
    elif spt[1] == "-RRB-":
        spt[0] = spt[1] = ")"
    elif spt[1] == "-LCB-":
        spt[0] = spt[1] = "{"
    elif spt[1] == "-RCB-":
        spt[0] = spt[1] = "}"


class ptb_loader:
    token_pattern = re.compile(r"\([^()]*\)")

    def load(path):
        sentence_set = {}
        ptb = open(path, "r")
        doc = re.search(r"\\wsj_(\d*)\.mrg", path).groups()[0]
        index = -1

        for line in ptb:
            if line[0] == "(":
                if index != -1:
                    sentence_set[doc + addZeros(index)] = sent
                sent = []
                index += 1

            tokens = ptb_loader.token_pattern.findall(line)
            for token in tokens:
                spt = token.split(" ")
                spt[0] = spt[0][1:]
                spt[1] = spt[1][:-1]

                # special cases
                special_transform(spt)

                sent.append(spt)

        sentence_set[doc + addZeros(index)] = sent
        return sentence_set

class wsj_loader:
    token_pattern = re.compile(r"\([^()]*\)")

    def load(path):
        sentence_set = {}

        wsj = open(path, "r")
        doc = re.search(r"\\wsj_(\d*)\.parse", path).groups()[0]
        index = -1

        for line in wsj:
            if line[0] == "(":
                if index != -1:
                    sentence_set[doc + addZeros(index)] = sent
                sent = []
                index += 1

            tokens = wsj_loader.token_pattern.findall(line)
            for token in tokens:
                spt = token.split(" ")
                spt[0] = spt[0][1:]
                spt[1] = spt[1][:-1]

                # special cases
                special_transform(spt)

                sent.append(spt)

        sentence_set[doc + addZeros(index)] = sent
        return sentence_set


class deep_loader:
    punct_list = [",", ".", "\"", "'", ":", "-", "$", "{", "}", ")", "(", "-NONE-"]

    def set_src(src):
        deep_loader.wsj = src

    # use ptb3 file to fit ON5
    def wsj_comleter(root_path):
        wsj = deep_loader.wsj
        temp = -1
        keys = list(wsj.keys())
        keys.sort()
        for index in keys:
            if temp == -1:
                temp = int(index) // 1000
            else:
                while temp + 1 < int(index) // 1000:
                    temp += 1
                    wsj.update(ptb_loader.load(
                        root_path + "\\{}\\wsj_{}.mrg".format("0" * (2 - len(str(temp // 100))) + str(temp // 100),
                                                              "0" * (4 - len(str(temp))) + str(temp))))
                temp = int(index) // 1000

    # Convert token location tags in deepbank resource to semlink
    # Return True when success, else False
    def convert(sentence):
        starts = {}
        wsj = deep_loader.wsj[sentence["doc"] + sentence["sent"]]
        ends = {}
        ender = 0
        src = sentence['src']

        for tag in range(len(wsj)):
            token = wsj[tag]
            token[1] = token[1].replace(r"\/", r"/")
            if token[0] != "-NONE-":
                if token[1] == "...":
                    token[1] = ". . ."
                starter = src.find(token[1], ender)

                # detect missing word
                if starter == -1:
                    print("Error: Token Missing in sent." + sentence["doc"] + sentence["sent"])
                    # print("searching token:", tag, token[1], ";  missing after:", ender)
                    return False

                # detect skip word
                if starter - ender > 1:
                    print("Error: Token Skipping in sent." + sentence["doc"] + sentence["sent"])
                    # print(sentence["src"])
                    # print(tag, token[1], starter, ender)
                    return False

                ender = starter + len(token[1])
                starts[str(starter)] = tag
                ends[str(ender)] = tag

        for node in sentence["nodes"]:
            try:
                node[2] = starts[node[2]]
                node[3] = ends[node[3]]

                while wsj[node[3]][0] in deep_loader.punct_list and node[2] < node[3]:
                    node[3] -= 1

                while wsj[node[2]][0] in deep_loader.punct_list and node[2] < node[3]:
                    node[2] += 1

                node[3]+=1 #End Pos should add one for sliding

            except Exception as arg:
                print("Error: Deepbank Word-Seg Mistake in sent." + sentence["doc"] + sentence["sent"],
                      "at token." + arg.args[0])
                # print(sentence["src"])
                # print("At the node: ", node)
                return False

        return True

    attr = []

    def load(path):
        sentence_set = {}
        with gzip.open(path, 'r') as pf:
            sentence = {}
            nodes = []
            flag = False
            for line in pf:
                line = line.decode('utf-8')
                if line[0] == "}":
                    sentence["nodes"] = nodes
                    break

                matcher = re.match(r"\[\d*\] \(\d of \d\) \{\d\} `(.*)'", line)
                if matcher is not None:
                    sentence["src"] = matcher.groups()[0]

                    # special rules
                    if sentence["src"][-4:] == "U.S.":
                        sentence["src"] += "."
                    if sentence["src"][-5:] == 'U.S."':
                        sentence["src"] = sentence["src"][:-1] + '."'

                if flag:
                    node = list(re.search(r"(.*):(.*)<(\d*):(\d*)>(.*)", line.strip()).groups())
                    nodes.append(node)

                matcher = re.search(r"^{", line)
                if matcher:
                    sentence["head"] = line[1:-2]
                    flag = True

            matcher = re.search(r"\\2(\d{4})(\d{3}).gz", path).groups()
            sentence["doc"] = matcher[0]
            sentence["sent"] = matcher[1]

            if deep_loader.convert(sentence):
                sentence_set[matcher[0] + matcher[1]] = sentence
        return sentence_set


# Given deepbank verb type and semlink verb type, check whether they are exclusively match
class verb_checker:
    # There are two schemes, 1st is map db-type to its first corresponding sl-type;
    # 2nd is map sl-type to its first corresponding db-type
    # We seperately save them in two groups of variables.
    # List "errors" is used for recording error verb types for final output (only if withlog switch is on),
    #                   it only considers the 1st scheme （because we assume the 1st scheme is main scheme)
    # Input: String target (select "verbnet" or "framenet" label for semlink),
    #        Boolean withlog (if True, automatically creating log file)
    def __init__(self, target="vb", withlog=False):
        self.linking1 = {}
        self.linking2 = {}
        self.bad_links1 = 0
        self.bad_links2 = 0
        self.total_verb = 0
        self.target = target
        self.errors = {}
        if withlog:
            self.f = open("verb_checking.log", "w")
        else:
            self.f = False

    # Apply 2 labels to 'process' procedure, write log if 'withlog' switch is on
    def apply(self, vern, label1, label2):
        if not self.process(label1, label2) and self.f:
            self.f.write("sent: {}-{}\ttoken: {}\ttype-1: {}\ttype-2: {}\tand\t{} (v.1st)\n".format(
                re.search(r"_(\d*)\.", verb["doc"]).groups()[0], verb["sent"],
                verb["token"], label1,
                label2, self.linking1[label1]))
            if label1 in self.errors.keys():
                self.errors[label1].append(label2)
            else:
                self.errors[label1] = [self.linking1[label1], label2]

    # Input: String db_type, List verb (of semlink)
    def check(self, db_type, verb):
        if self.target == "vb":
            self.total_verb += 1
            sl_type = verb["verb"] + ";" + verb["verbnet"]

            # If you want to switch scheme, change the sequence of sl_type and db_type here
            self.apply(verb, sl_type, db_type)

        else:
            assert (self.target == "fn")
            if verb["frame"] not in ["IN", "NF"]:
                self.total_verb += 1
                sl_type = verb["frame"]

                self.apply(verb, sl_type, db_type)

    # If match without problem, return True only if 1st scheme defeat, else return False
    # Input: String label1 (the label in corpus 1), String label2 (the label in corpus 2)
    def process(self, label1, label2):
        flag = True
        if label1 in self.linking1.keys():
            if label2 != self.linking1[label1]:
                self.bad_links1 += 1
                flag = False
        else:
            self.linking1[label1] = label2

        if label2 in self.linking2.keys():
            if label1 != self.linking2[label2]:
                self.bad_links2 += 1
        else:
            self.linking2[label2] = label1
        return flag

    # Show final result
    def show(self):
        print("Selecting {} label for Semlink, {} / {} of {} verbs match unconsistently.".format(self.target,
                                                                                                 self.bad_links1,
                                                                                                 self.bad_links2,
                                                                                                 self.total_verb))
        if self.f:
            self.f.write("========================Errors Records========================\n")

            for error in sorted(self.errors.keys(), key=lambda x: len(self.errors[x]), reverse=True):
                self.f.write(error + "\t" + str(len(self.errors[error])) + "\t" + str(
                    sorted(set(self.errors[error]), key=lambda x: self.errors[error].count(x), reverse=True)) + "\n")
            self.f.close()

#  sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]
#  deepbank_parser=["doc","sent","src","nodes","head"]

if __name__ == "__main__":
    print("========================Start Basic Checking=========================")
    deep_loader.set_src(traverse_dir(".\\data\\wsj\\00", wsj_loader))
    deep_loader.wsj_comleter(".\\data\\ptb3")
    sembank = traverse_dir(".\\data\\sembank\\00", sem_loader)
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

    for sent in sembank.keys():
        if sent in deepbank.keys():
            count += 1
            head, nodes, start_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"])
            allsafe = True
            for verb in sembank[sent]:
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


    print("Semlink size: {}, Deepbank size: {}".format(len(sembank), len(deepbank)))
    print("{} of {} verbs in all Semlink lacked FN link, in {} sentences totally.".format(sem_loader.framemiss,
                                                                                          sem_loader.total_verb,
                                                                                          sem_loader.framemiss_sentence))
    print("{} / {} / {} verbs in semlink are considered as (adj. / n. / unknown.) in deepbank.".format(type_error_adj, type_error_n,type_error_u))
    print("{} sentences matched between Semlink and Deepbank.".format(count))
    print("{} sentences are completely matched.".format(fullsent))
    vc.show()
