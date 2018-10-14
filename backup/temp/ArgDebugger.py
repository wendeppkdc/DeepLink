# This file is used for testing argument alignment problems
import re

class argmapper:
    arg_map={}
    arg_base={}

    def record(description,verb,db_type,argsafe,sent):
        #if description.find("=")>=0:
            #description = description[0:description.find("=")]
            #description = description[description.find("="):]
            #if description.find(";"):

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

    def show(deepbank):
        out_list={}

        for arg in sorted(list(argmapper.arg_map.keys()), key=lambda x: len(argmapper.arg_map[x]), reverse=True):
            if len(argmapper.arg_map[arg]) > 1:
                temp_head = {}
                temp_occur=set()
                for argd in argmapper.arg_map[arg]:
                    print(argd)
                    h = argd[:argd.find("-")]
                    if h in temp_occur:
                        temp_head[h]=[]
                    else:
                        temp_occur.add(h)

                for argd in argmapper.arg_map[arg]:
                    h = argd[:argd.find("-")]
                    if h in temp_head.keys():
                        temp_head[h].append(argd+"->"+arg)
                out_list.update(temp_head)
            #else:
            #    break

        error_total=0
        for verb in out_list:
            for arg in out_list[verb]:
                error_total+=len(argmapper.arg_base[arg])
                print("printing: "+arg+"\ttotal: "+str(len(argmapper.arg_base[arg])))
                for doc in argmapper.arg_base[arg]:
                    print(arg + '-' + doc)

                '''    nodes=[]
                    edges=[]
                    for node in deepbank[doc]["nodes"]:
                        nodes.append((node[0],node[1]))
                        source=re.search(r"\[(.*?)\]",node[4]).groups()[0]
                        source=source.split(", ")
                        for edge in source:
                            if len(edge)>0:
                                edge=edge.split(" ")
                                edges.append((edge[0],node[0],edge[1]))
                                graph_painter(arg+"-"+doc, nodes,edges)'''

        print(error_total)

    def write(output_path):
        out_list = {}
        valve=0.81
        final_link={}

        for arg in sorted(list(argmapper.arg_map.keys()), key=lambda x: len(argmapper.arg_map[x]), reverse=False):
            if len(argmapper.arg_map[arg]) > 1:
                temp_head = {}
                temp_occur = set()
                for argd in argmapper.arg_map[arg]:
                    h = argd[:argd.find("-")]
                    if h in temp_occur:
                        temp_head[h] = []
                    else:
                        temp_occur.add(h)

                for argd in argmapper.arg_map[arg]:
                    h = argd[:argd.find("-")]
                    if h in temp_head.keys():
                        temp_head[h].append(argd + "->" + arg)
                out_list.update(temp_head)
            else:
                final_link[list(argmapper.arg_map[arg])[0]]=arg

        for verb in out_list:
            total=0
            for arg in out_list[verb]:
                total+=len(argmapper.arg_base[arg])
            for arg_pair in out_list[verb]:
                arg = arg_pair.split("->")
                _, argp = arg[1].split("-v-")
                argd = arg[0][arg[0].find("-")+1:]

                #delete argM
                if re.match(r"ARG\d$",argp) is None:
                    continue
                if re.match(r"ARG\d$",argd) is None:
                    continue

                #domimant correspondence
                if len(argmapper.arg_base[arg_pair])>valve*total:
                    final_link[arg[0]]=arg[1]
                else:
                    #argd==argp+1
                    if int(argp[-1])+1==int(argd[-1]):
                        final_link[arg[0]]=arg[1]

        f=open(output_path,"w")
        f.write("db-predicate\tdb-arg\tpb-predicate\tpb-arg\n")
        for term in final_link.keys():
            print(final_link[term])
            v_loc=final_link[term].find("-",final_link[term].find("-")+1)
            f.write(term.split("-")[0]+"\t"+term.split("-")[1]+"\t"
                    +final_link[term][:v_loc]+"\t"+final_link[term][v_loc+1:]+"\n")
        f.close()

    #TODO complete this part
    def read(inputpath):
        pass