#This file is used for loading predicate matrix
class PMLoader:

    #pb_index用于存储pb group-fn frame键值对
    #fe_index用于存储pb role-fn frame element键值对
    pb_index={}
    fe_index={}

    def init(filepath):
        f=open(filepath,"r")
        for line in f:
            terms=line.strip().split("\t")
            record={}

            if terms[0]=="id:eng" and terms[1]=="id:v":
                record["verb"]=terms[2][3:]
                record["vn"]=terms[6][3:]
                if record["vn"]=="NULL":
                    record["vn"]=terms[5][3:]
                record["fn"]=terms[12][3:]
                record["pb"]=terms[15][3:]
                fnarg=terms[14][3:]
                pbarg="ARG"+terms[16][3:]
                if fnarg=="NULL" or pbarg=="ARGNULL":
                    continue
                PMLoader.pb_index[record["pb"]]=record["fn"]
                PMLoader.fe_index[record["pb"]+pbarg]=fnarg

    def getFE(pb,pbarg):
        if pb+pbarg in PMLoader.fe_index.keys():
            return "fn."+PMLoader.fe_index[pb+pbarg]
        else:
            return "pb."+pbarg

    def getFrame(pb):
        if pb in PMLoader.pb_index.keys():
            return "fn."+PMLoader.pb_index[pb]
        else:
            return "pb."+pb