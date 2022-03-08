from click import style
import pygraphviz as pgv
from SystemDependenceGraph.DependenceNode import *

class Graph:

    def __init__(self):
        self.nodes = []
        self.builder = {}

    def draw(self, path):
        G = pgv.AGraph(directed=True, strict=False)
        nlist = [str(n)+" mem: "+str(id(n)) for n in self.nodes]

        G.add_nodes_from(nlist)

        for n in self.nodes:
            if isinstance(n, CondNode):
                for c in n.true_statements:
                    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), color="blue")
                for c in n.false_statements:
                    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), color="red")

            else:
                for c in n.get_children():
                    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)))
            #for c in n.get_inter_children():
            #    G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), style="dashed")
            for c in n.get_fictitious_children():
                G.add_edge(str(n)+" mem: "+str(id(n)), str(c)+" mem: "+str(id(c)), style="dotted")

        G.draw(path=path, prog="neato")

    def get_nodes(self):
        return self.nodes