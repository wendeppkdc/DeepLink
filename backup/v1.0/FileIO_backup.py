import os
import os.path
import gzip
import re
from GraphUtils import *
import random
import pickle

#(document_id) (sentence number) (token number) (standard) (verb-v) (VerbNet class)
#  (Framenet Frame) (PB grouping) (SI grouping) (tense/aspect/mood info)
#  (ArgPointer)-ARGX=(VN Role);(FN Role/Optional Extra Fn Roles)
sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]

#nodes is a list of node, node is list of
# [hanlde, class, startpoint(token ord), endpoint(token ord, not include), extra information] (all elements are strings)
deepbank_parser=["doc","sent","src","nodes","head"]

sembank={}
deepbank={}

def traverse_dir(path, operator):
    sentenceSet={}
    parents = os.listdir(path)
    for parent in parents:
        child = os.path.join(path, parent)
        if os.path.isdir(child):
            sentenceSet.update(traverse_dir(child,operator))
        else:
            sentenceSet.update(operator.load(child))
    return sentenceSet


def addZeros(num):
    s=str(int(num)+1)
    return "0"*(3-len(s))+s

def alignment()

class sem_loader:
    framemiss=0
    framemiss_sentence=0
    token_pattern=re.compile(r"\([^()]*\)")

    #convert extended index to source index
    def converter(ptb_path, operator="e2s"):
        assert(operator=="e2s" or operator=="s2e")
        convert = None
        try:
            ptb = open(ptb_path, "r")
        except IOError:
            return None
        for line in ptb:
            if line[0] == "(":
                if convert is not None:
                    convert.append(index)
                else:
                    convert = []
                index = {}
                source = -1
                extended = -1

            tokens = sem_loader.token_pattern.findall(line)
            for token in tokens:
                spt = token.split(" ")
                assert (len(spt) == 2)
                extended += 1
                if not re.match(r"\(-NONE-", spt[0]):
                    source += 1
                if operator=="e2s":
                    index[str(extended)]=str(source)
                else:
                    index[str(source)]=str(extended)
        convert.append(index)
        return convert

    def load(path):
        sentence_set = {}
        with open(path,"r") as file:
            doc = re.search(r"\_(.*)\.", path).groups()[0]
            sent="-1"
            verbs=None
            for line in file:
                args=line.strip().split(" ")
                sentence = {}
                sentence["doc"]=doc
                for index in range(10):
                    sentence[sem_parser[index]]=args[index]
                args=args[10:]
                sentence["args"]=args
                if sent=="-1":
                    sent=sentence["sent"]
                    verbs=[]
                    miss=False

                if sentence["frame"] in ["IN","NF"]:
                    sem_loader.framemiss+=1
                    miss=True

                if sent!=sentence["sent"]:
                    if miss:
                        sem_loader.framemiss_sentence+=1
                    sentence_set[doc+addZeros(sent)]=verbs
                    sent=sentence["sent"]
                    verbs=[]
                    verbs.append(sentence)
                    miss=False
                else:
                    verbs.append(sentence)

            sentence_set[doc+addZeros(sent)]=verbs
            if miss:
                sem_loader.framemiss_sentence += 1

        return sentence_set

class deep_loader:
    '''def split_checker(wsj, sentence, sum):
    doc=sentence["doc"]
    try:
        src=open(".\\data\\wsj\\{}\\wsj_{}.parse".format(doc[:2], doc[:4]))
    except IOError:
        return None
        #src=open(".\\data\\ptb3\\{}\\wsj_{}.mrg".format(doc[:2], doc[:4]))
    if sentence["doc"] + sentence["sent"] in wsj.keys():
        splited = wsj[sentence["doc"] + sentence["sent"]]
    else:
        return None
    if len(splited) == sum:
        return True
    else:
        return False'''

    attr=[]

    def load(path):
        sentence_set={}
        with gzip.open(path, 'r') as pf:
            sentence = {}
            nodes=[]
            startTokens={}
            endTokens={}
            flag=False
            srcFlag=True
            src=[]
            for line in pf:
                line = line.decode('utf-8')
                if line[0]=="}":
                    sentence["nodes"]=nodes
                    break

                if srcFlag:
                    matcher=re.search(r"\(\d*?, (\d*?), (\d*?), <(\d*?):(\d*?)>, (\d*?), \"(.*?)\",.*\)",line)
                    if matcher:
                        assert((int(matcher.groups()[0])+1)==(int(matcher.groups()[1])))
                        assert(matcher.groups()[4]=="1")
                        startTokens[matcher.groups()[2]] = matcher.groups()[0]
                        endTokens[matcher.groups()[3]] = matcher.groups()[1]
                        src.append(matcher.groups()[5])

                if srcFlag and line[0]==">":
                    srcFlag = False
                    sentence["src"]=src

                if flag:
                    node=list(re.search(r"(.*):(.*)<(\d*):(\d*)>(.*)", line.strip()).groups())
                    assert(node[2] in startTokens.keys())
                    assert(node[3] in endTokens.keys())
                    node[2]=startTokens[node[2]]
                    node[3]=endTokens[node[3]]
                    nodes.append(node)

                matcher=re.search(r"^{",line)
                if matcher:
                    sentence["head"]=line[1:-2]
                    flag=True

            matcher=re.search(r"\\2(\d{4})(\d{3}).gz",path).groups()
            sentence["doc"]=matcher[0]
            sentence["sent"]=matcher[1]

            sentence_set[matcher[0]+matcher[1]]=sentence
        return sentence_set


''' 
#testing dataset length
if __name__=="__main__":
    sem=traverse_dir(".\\data\\sembank\\00",sem_loader)
    deep=traverse_dir(".\\data\\deepbank\\wsj00",deep_loader)
    print(len(sem),sem_loader.gap)
    print(len(deep))
'''

#  sem_parser=["doc","sent","token","stand","verb","verbnet","frame","PB","SI","TAM","args"]
#  deepbank_parser=["doc","sent","src","nodes","head"]

if __name__=="__main__":
    sembank=traverse_dir(".\\data\\sembank\\00",sem_loader)
    deepbank=traverse_dir(".\\data\\deepbank\\wsj00",deep_loader)

    count=0
    endmiss=0
    startmiss=0
    fullsent=0
    src_loss=0
    for sent in sembank.keys():
        if sent in deepbank.keys():
            convert=sem_loader.converter(".\\data\\wsj\\{}\\wsj_{}.parse".format(sent[:2],sent[:4]))
            if convert is None:
                src_loss+=1
                convert=sem_loader.converter(".\\data\\ptb3\\{}\\wsj_{}.mrg".format(sent[:2],sent[:4]))

            count+=1
            head, nodes, start_list = deep_grapher(deepbank[sent]["nodes"], deepbank[sent]["head"])
            allsafe = True
            for verb in sembank[sent]:
                for arg in verb["args"]:
                    pointers, scription = re.match(r"(.*?)-(.*)",arg).groups()

                    pointers=re.split("[;\*,]",pointers)
                    for pointer in pointers:
                        start, end=re.match(r"(\d*):(\d*)",pointer).groups()
                        start=convert[int(sent[4:])-1][start]
                        if start not in start_list:
                            if start-1 in
                            print("startpoint missmatched.")
                            print(sent)
                            print(convert[int(sent[4:])-1])
                            print(start,scription)
                            startmiss+=1
                            allsafe=False
                        else:
                            success=False
                            end=str(int(start)+int(end))
                            '''if end not in convert[int(sent[4:]) - 1].keys():
                                print("semlink out of PTB range.")
                                continue
                                allsafe = False'''
                            end = str(int(convert[int(sent[4:]) - 1][end])+1)

                            for candidate in start_list[start]:
                                if candidate.addr[1]==end:
                                    success=True
                                    break
                            if not success:
                                '''print("endpoint missmatched.")
                                print(sent)
                                print(end,scription)'''
                                endmiss+=1
                                #allsafe=False

            if allsafe:
                fullsent+=1

    print("Semlink size: {}, Deepbank size: {}".format(len(sembank), len(deepbank)))
    print("{} verbs mismatched with FN, in {} sentences totally.".format(sem_loader.framemiss, sem_loader.framemiss_sentence))
    print("{} sentences don't have source in Ontonotes5.0,".format(src_loss))
    print("{} sentences matched between Semlink and Deepbank. {}, {} (startpoint / endpoint) arguments missmatched.".format(count,startmiss, endmiss))
    print("{} sentences are completely matched.".format(fullsent))