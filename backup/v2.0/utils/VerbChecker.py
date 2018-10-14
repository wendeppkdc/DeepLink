# Given deepbank verb type and semlink verb type, check whether they are one-to-one correspondent
import re

class verb_checker:
    # There are two schemes, 1st is map db-type to its first corresponding sl-type;
    # 2nd is map sl-type to its first corresponding db-type
    # We seperately save them in two groups of variables.
    # List "errors" is used for recording error verb types for final output (only if withlog switch is on),
    #                   it only considers the 1st scheme (because we assume the 1st scheme is main scheme)
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
    def apply(self, verb, label1, label2):
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