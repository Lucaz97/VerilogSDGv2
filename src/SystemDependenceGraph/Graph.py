from SystemDependenceGraph.DependenceNode import *
from os.path import exists

class Graph:

    def __init__(self):
        self.nodes = []
        self.builder = {}

    #def draw(self, path):
    #    G = pgv.AGraph(directed=True, strict=False)
    #    nlist = [str(n)+" mem: "+str(id(n)) for n in self.nodes]

    #    G.add_nodes_from(nlist)
    #    feature_file = open(path+"_features.txt", 'w')

    #     for n in self.nodes:
    #         print(n)
    #         print(encode_node(n), file=feature_file)
    #         if isinstance(n, CondNode):
    #             for c in n.true_statements:
    #                 G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), color="blue")
    #             for c in n.false_statements:
    #                 G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), color="red")

    #         else:
    #             for c in n.get_children():
    #                 G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)))
    #         #for c in n.get_inter_children():
    #         #    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), style="dashed")
    #         for c in n.get_fictitious_children():
    #             G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), style="dotted")

    #     G.draw(path=path, prog="neato") 

    def get_nodes(self):
        return self.nodes

    def print_graph(self, path, index=0):

        if exists(path+"_features.txt"):
            feature_file = open(path+"_features.txt", 'a')
            cell_file = open(path+"_cells.txt", 'a')
            link_train_file = open(path+"_link_train.txt", 'a')
            link_test_file = open(path+"_link_test.txt", 'a')
            link_test_n_file = open(path+"_link_test_n.txt", 'a')
        else:
            feature_file = open(path+"_features.txt", 'w')
            cell_file = open(path+"_cells.txt", 'w')
            link_train_file = open(path+"_link_train.txt", 'w')
            link_test_file = open(path+"_link_test.txt", 'w')
            link_test_n_file = open(path+"_link_test_n.txt", 'w')

        for i, n in enumerate(self.nodes):
            # print(n)
            print(encode_node(n), file=feature_file)
            print(n, file=cell_file)
            if isinstance(n, CondNode) and "locking_key" in n.cond_statement.get_cond_dependencies():
                for c in n.true_statements:
                    print(i+index, self.nodes.index(c)+index, file=link_test_file)
                for c in n.false_statements:
                    print(i+index, self.nodes.index(c)+index, file=link_test_n_file)
            else:
                for c in n.get_children():
                    print(i+index, self.nodes.index(c)+index, file=link_train_file)
            #for c in n.get_inter_children():
            #    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), style="dashed")
            for c in n.get_fictitious_children():
                print(i+index, self.nodes.index(c)+index, file=link_train_file)

        link_train_file.close()
        link_test_n_file.close()
        link_test_file.close()
        cell_file.close()
        feature_file.close()

        print("!FINAL_INDEX! :", i+index)