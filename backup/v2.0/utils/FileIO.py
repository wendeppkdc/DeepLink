import os
import os.path
from loaders.PMLoader import PMLoader as pm
from loaders.DeepLoader import deep_loader
from loaders.SemLoader import sem_loader
from loaders.PTBLoader import ptb_loader
from loaders.ONCompleter import on_comleter
from utils.Matcher import DB_SL_matcher
from utils.Converter import DB_PM_converter

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
    pm.init(".\\data\\pm\\PredicateMatrix.v1.3.txt")
    print("Basic Checking Complete.")
    print("Semlink size: {}, Deepbank size: {}".format(len(semlink), len(deepbank)))
    print("{} of {} verbs in all Semlink lacked FN link, in {} sentences totally.".format(sem_loader.framemiss,
                                                                                          sem_loader.total_verb,
                                                                                          sem_loader.framemiss_sentence))
    print()

    #DB_SL_matcher(deepbank,semlink,wsj, False)
    DB_PM_converter(deepbank)