# Deal with speical cases in PTB (WSJ) file
# Transport label to real token

def special_transform(spt0, spt1):
    if spt1 == "``" or spt1 == "''":
        spt0 = spt1 = "\""
    elif spt1 == "-LRB-":
        spt0 = spt1 = "("
    elif spt1 == "-RRB-":
        spt0 = spt1 = ")"
    elif spt1 == "-LCB-":
        spt0 = spt1 = "{"
    elif spt1 == "-RCB-":
        spt0 = spt1 = "}"

    return spt0, spt1
