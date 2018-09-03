# This Procedure is used for extracting tokens from semlink file (semlink 1.2.2 style)
# The file format is like this:
# (document_id) (sentence number) (token number) (standard) (verb-v) (VerbNet class)
#  (Framenet Frame) (PB grouping) (SI grouping) (tense/aspect/mood info)
#  (ArgPointer)-ARGX=(VN Role);(FN Role/Optional Extra Fn Roles)
import re
from loaders.AddZeros import addZeros
sem_parser = ["doc", "sent", "token", "stand", "verb", "verbnet", "frame", "PB", "SI", "TAM", "args"]

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
