# It imports ptb_loader to extract tokens from PTB3,
#          in order to deal with file missing from Ontonotes5.0

from loaders.PTBLoader import ptb_loader

# use ptb3 file to fit ON5
def on_comleter(wsj, root_path):
    temp = -1
    keys = list(wsj.keys())
    keys.sort()
    for index in keys:
        if index[0]=="t":
            continue

        if temp == -1:
            temp = int(index) // 1000
        else:
            while temp + 1 < int(index) // 1000:
                temp += 1
                wsj.update(ptb_loader.load(
                    root_path + "\\{}\\wsj_{}.mrg".format("0" * (2 - len(str(temp // 100))) + str(temp // 100),
                                                          "0" * (4 - len(str(temp))) + str(temp))))
            temp = int(index) // 1000