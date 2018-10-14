# This file is used for testing argument alignment problems
import re

class argmapper:
    arg_map={}
    group_map={}
    arg_base={}
    total=0

    def record(description,verb,db_type,argsafe,sent):
        #if description.find("=")>=0:
            #description = description[0:description.find("=")]
            #description = description[description.find("="):]
            #if description.find(";"):

        if re.match(r"LINK-",description) is not None:
            return

        sem_arg = verb["PB"] + '-' + description
        db_arg = db_type + "-" + argsafe
        if db_arg in argmapper.arg_map.keys():
            argmapper.arg_map[db_arg].add(sem_arg)
        else:
            argmapper.arg_map[db_arg] = {sem_arg}

        if db_arg+"->"+sem_arg in argmapper.arg_base.keys():
            argmapper.arg_base[db_arg+"->"+sem_arg].append(sent)
        else:
            argmapper.arg_base[db_arg+"->"+sem_arg]=[sent]
        argmapper.total+=1

    def show(deepbank):
        error_total = 0
        error_type=0
        type_total=0

        for argd in sorted(list(argmapper.arg_map.keys()), key=lambda x: len(argmapper.arg_map[x]), reverse=True):
            type_total+=1
            if len(argmapper.arg_map[argd]) > 1:
                error_type+=1
                for args in argmapper.arg_map[argd]:
                    error_total+=len(argmapper.arg_base[argd+"->"+args])
                    print("printing: "+argd+"->"+args+"\ttotal: "+str(len(argmapper.arg_base[argd+"->"+args])))
                    for doc in argmapper.arg_base[argd+"->"+args]:
                        print(doc+"\t")

        print("{} error arguments ({} in all) are collected.".format(error_total,argmapper.total))
        print("{} types of arguments ({} in all).".format(error_type,type_total))

    def write(output_path):
        out_list = {}
        valve=0.81
        final_link={}

        for argd in sorted(list(argmapper.arg_map.keys()), key=lambda x: len(argmapper.arg_map[x]), reverse=False):
            if len(argmapper.arg_map[argd]) > 1:
                total=0
                for argp in argmapper.arg_map[argd]:
                    total+=len(argmapper.arg_base[argd+"->"+argp])

                for argp in argmapper.arg_map[argd]:
                    argp_v = argp[:argp.find("-")]
                    argp_arg=argp[argp.find("-")+1:]
                    argd_v=argd[:argd.find("-")]
                    argd_arg = argd[argd.find("-") + 1:]

                    #delete argM
                    #//TODO what about argM?
                    if re.match(r"ARG\d$",argp_arg) is None:
                        continue
                    if re.match(r"ARG\d$",argd_arg) is None:
                        continue

                    #domimant correspondence
                    if len(argmapper.arg_base[argd+"->"+argp])>valve*total:
                        final_link[argd]=argp
                    else:
                        #argd==argp+1
                        if int(argp[-1])+1==int(argd[-1]):
                            final_link[argd]=argp
            else:
                final_link[argd]=list(argmapper.arg_map[argd])[0]

        f=open(output_path,"w")
        f.write("db-predicate\tdb-arg\tpb-predicate\tpb-arg\ttotal_num\n")
        for term in final_link.keys():
            v_loc=final_link[term].find("-")
            f.write(term.split("-")[0]+"\t"+term.split("-")[1]+"\t"
                    +final_link[term][:v_loc]+"\t"+final_link[term][v_loc+1:]+"\t"
                    +str(len(argmapper.arg_base[term+"->"+final_link[term]]))+"\n")
        f.close()

    #TODO complete this part
    def read(inputpath):
        f=open(inputpath,"r")
        for line in f:
            line=line.split("\t")
            argmapper.arg_map[line[0]+"-"+line[1]]=line[2]+line[3]
            argmapper.group_map[line[0]]=line[2]

    def getPBG(dbv):
        if dbv in argmapper.group_map.keys():
            return argmapper.group_map[dbv]
        else:
            return False

    def getPBR(arg):
        if arg in argmapper.arg_map.keys():
            return argmapper.arg_map[arg]
        else:
            return False