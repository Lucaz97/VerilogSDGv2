from SystemDependenceGraph.ProgramDependencyGraph import *
from SystemDependenceGraph.visit import *
from SystemDependenceGraph.modulevisitor import *
from SystemDependenceGraph.signalvisitor import *
from SystemDependenceGraph.DependenceNode import *
from SystemDependenceGraph.Graph import *
from copy import deepcopy

class SystemDependencyGraph(Graph):
    def __init__(self, ast, topmodule): 
        super().__init__()
        self.mv = ModuleVisitor()
        self.mv.visit(ast)
        self.flattened_sdgs = {}
        self.topmodule = topmodule

        modulenames = self.mv.get_modulenames()
        self.modules_sdg = {}
        for module in modulenames:
            mod_node = self.mv.get_moduleinfotable().getDefinition(module)
            av = ArrayVisitor(mod_node)
            print("ARRAYS MODULE", module, ":" , av.arrays)
            sv = SignalVisitor(av.arrays, self.mv.get_moduleinfotable())
            sv.visit(mod_node)
            msdg = ModuleSystemDependencyGraph(sv, module)
            msdg.build()
            self.modules_sdg[module] = msdg
        
        self.nodes = self.flatten_sdg(topmodule)
        
    def draw_modules(self):
        for msdg in self.modules_sdg.values():
            msdg.draw(msdg.name)

    def get_inputs(self):
        return [node for node in self.nodes[0].get_children() if isinstance(node, InputNode) and node.label not in ["clk", "rst", "reset", "clock"]]

    def flatten_sdg(self, topmodule):
        fsdg_nodes = []
        # check if topmodule is in flattened sdgs
        if topmodule in self.flattened_sdgs:
            return clone_nodelist(self.flattened_sdgs[topmodule])
        
        # if not flatten then add to flattened sdgs
        # check topmodule nodelist
        for node in self.modules_sdg[topmodule].clone():
            if isinstance(node, InstanceNode):
                 # for each instance node, flatten instance module then  add a copy of each node of instance graph to this graph
                 for sub_node in self.flatten_sdg(node.get_modulename()):
                    fsdg_nodes.append(sub_node)
                    if isinstance(sub_node, ParameterNode): 
                        sub_node.parents = [fsdg_nodes[0]]
                        fsdg_nodes[0].add_child(sub_node)
                    elif isinstance(sub_node, InputNode):
                        print(sub_node, node.get_modulename())
                        if sub_node.label == None:
                            print("LABEL IS NONE:", sub_node)
                            quit()
                        # need to find coupling node from parents of the instance node. 
                        for n in node.get_parents(): 
                            if isinstance(n, CouplingNode) and sub_node.label == n.invar:
                                n.children = [sub_node]
                    elif isinstance(sub_node, OutputNode):
                        # need to find coupling node from parents of the instance node. 
                        for n in node.get_parents(): 
                            if isinstance(n, CouplingNode) and sub_node.label == n.invar:
                                if node in n.children:
                                    n.children.remove(node)
                                n.add_parent(sub_node)
                                sub_node.add_child(n)

            else:
                # This graph is equal to topmodule graph for except of instance nodes.
                fsdg_nodes.append(node)
        return fsdg_nodes   
        # connect copling nodes
        # reconnect always and parameters of instance graph to top graph






class ModuleSystemDependencyGraph(Graph):
    
    def __init__(self, signalvisitor, name):
        super().__init__()
        self.signalvisitor = signalvisitor
        self.name = name
        self.coupling_nodes = []

    def import_pdg(self, pdg):
        for n in pdg.get_nodes():
            self.nodes.append(n)
        self.builder.update(pdg.get_builder())

    def build(self):
        # import always
        for a in self.signalvisitor.get_always():
            pdg = ProgramDependencyGraph(a)
            pdg.build()
            self.import_pdg(pdg)

        # # import functions
        # for f in self.signalvisitor.get_functions():
        #     pdg = ProgramDependencyGraph(f)
        #     pdg.build()
        #     self.import_pdg(pdg)
        #     # need to add input nodes and output node
        #     for inp in f.get_inputs():
        #         inode = InputNode(inp) # TODO FINISH THIS

        self.build_nodes()
        self.build_edges()
        self.connect_orphans()

    def build_nodes(self):
        # build module node
        mod_node = ModuleNode(self.name)
        # insert module node in first position to be able to get this easily
        self.nodes.insert(0,mod_node)

        for a in self.signalvisitor.get_always():
            self.builder[a].add_fictitious_parent(mod_node)
            mod_node.add_fictitious_child(self.builder[a])

        # build a node for each assign statement
        for a in self.signalvisitor.get_assigns():
            node = AssignNode(str(a))
            node.set_ast(a.rhs_ast)
            self.nodes.append(node)
            self.builder[a] = node
            for c in a.get_consts():
                const_node = ConstNode(c)
                self.nodes.append(const_node)
                const_node.add_child(node)
                node.add_parent(const_node)

        # build a node for each parameter
        for p in self.signalvisitor.get_parameters():
            pnode = ParameterNode(p.get_name(), p.get_ids(), p.get_consts())
            self.nodes.append(pnode)
            self.builder[p] = pnode
            # connect parameter with module node
            pnode.add_fictitious_parent(mod_node)
            mod_node.add_fictitious_child(pnode)

        # immediately build edges between Parameters
        for p1 in self.signalvisitor.get_parameters():
            for p2 in self.signalvisitor.get_parameters(): 
                if p1 != p2 and p2.name in p1.get_ids():
                    # ids in parameters can only be other parameters ids
                    # dep from p2 to p1
                    self.builder[p2].add_child(self.builder[p1])
                    self.builder[p1].add_parent(self.builder[p2])

        # build a node for each instance and build coupling nodes
        for i in self.signalvisitor.get_instances():
            #build instance ndoe
            i_node = InstanceNode(i.get_module())
            self.nodes.append(i_node)
            self.builder[i] = i_node
            for couple in i.get_portlist():
                if couple[1]:
                    c_node = CouplingNode(couple[0], couple[1])
                    self.nodes.append(c_node)
                    self.coupling_nodes.append(c_node)
                    # i cant put these in buider but i know that the only direct 
                    # parents/childreen of instance are coupling nodes
                    
                    # we do not have information here to know if ports are inputs or
                    # outputs so we just connect them as inputs arbitrarily 
                    # and then check the direction when performing flatening

                    i_node.add_parent(c_node)
                    c_node.add_child(i_node)

        # build input and output nodes
        # INPUT
        for inp in self.signalvisitor.get_inputs():
            i_node = InputNode(inp)
            self.nodes.append(i_node)
            self.builder[inp] = i_node
            i_node.add_parent(mod_node)
            mod_node.add_child(i_node)

            for a in self.signalvisitor.get_always():
                for s in a.get_flattened_statements():
                    if(isinstance(s, AssignStruct) and inp in s.get_dependency_signals()) or ((isinstance(s, IfStruct) or isinstance(s, CaseStatementStruct)) and inp in s.get_cond_dependencies()):
                        self.builder[s].add_parent(i_node)
                        i_node.add_child( self.builder[s])
            for a in self.signalvisitor.get_assigns():
                if inp in a.get_dependency_signals():
                    self.builder[a].add_parent(i_node)
                    i_node.add_child( self.builder[a])
        # OUTPUT
        for out in self.signalvisitor.get_outputs():
            o_node = OutputNode(out)
            self.nodes.append(o_node)
            self.builder[out] = o_node

            for a in self.signalvisitor.get_always():
                for s in a.get_flattened_statements():
                    if isinstance(s, AssignStruct) and out in s.lhs_signals:
                        self.builder[s].add_child(o_node)
                        o_node.add_parent( self.builder[s])
            for a in self.signalvisitor.get_assigns():
                if out in a.lhs_signals:
                    self.builder[a].add_child(o_node)
                    o_node.add_parent( self.builder[a])

    def build_edges(self):
        # add edges to parameter -> foreach parameter check all asigns and all always rhs and cond signals
        for p in self.signalvisitor.get_parameters():
            for a in self.signalvisitor.get_always():
                for s in a.get_flattened_statements():
                    if isinstance(s, AssignStruct) and p.name in s.rhs_signals:
                        self.builder[p].add_child(self.builder[s])
                        self.builder[s].add_parent(self.builder[p])
                    elif (isinstance(s, IfStruct) or isinstance(s, CaseStatementStruct)) and p.name in s.get_cond_dependencies():
                        self.builder[p].add_child(self.builder[s])
                        self.builder[s].add_parent(self.builder[p])
            for a in self.signalvisitor.get_assigns():
                if p.name in a.rhs_signals:
                    self.builder[p].add_child(self.builder[a])
                    self.builder[a].add_parent(self.builder[p])
                
        # input edges are already done
        # connect assigns with assigns
        for a1 in self.signalvisitor.get_assigns():
            for a2 in self.signalvisitor.get_assigns():
                if a1 != a2 and [i for i in a1.lhs_signals if i in a2.rhs_signals]:
                    self.builder[a1].add_child(self.builder[a2])
                    self.builder[a2].add_parent(self.builder[a1])
        
        # connect assigns with always
        # if dependency check sens list if in sensilist direct dependency otherwise intercycle dependency
        for a1 in self.signalvisitor.get_assigns():
            for always in self.signalvisitor.get_always():
                for s in always.get_flattened_statements():
                    if (isinstance(s, AssignStruct) and [i for i in a1.lhs_signals if i in s.rhs_signals]) or ((isinstance(s, IfStruct) or isinstance(s, CaseStatementStruct)) and [i for i in a1.lhs_signals if i in s.get_cond_dependencies()]):
                        # we have dependency, check if direct or intercycle
                        if a1 in always.get_sensList():
                            # direct dependency
                            self.builder[a1].add_child(self.builder[s])
                            self.builder[s].add_parent(self.builder[a1])
                        else:
                            # itercycle dependency
                            self.builder[a1].add_inter_child(self.builder[s])
                            self.builder[s].add_inter_parent(self.builder[a1])
                    # check opposite direction
                    if isinstance(s, AssignStruct) and [i for i in s.lhs_signals if i in a1.rhs_signals]:
                        # direct dependency
                        self.builder[s].add_child(self.builder[a1])
                        self.builder[a1].add_parent(self.builder[s])
        # connect always with always
        for i, always1 in enumerate(self.signalvisitor.get_always()):
            for s1 in always1.get_flattened_statements():
                for always2 in self.signalvisitor.get_always()[i+1:]:
                    for s2 in always2.get_flattened_statements():
                        if isinstance(s1, AssignStruct):
                            if (isinstance(s2, AssignStruct) and [i for i in s1.lhs_signals if i in s2.rhs_signals]) or ((isinstance(s2, IfStruct) or isinstance(s2, CaseStatementStruct)) and [i for i in s1.lhs_signals if i in s2.get_cond_dependencies()]):
                                # we have dependency, check if direct or intercycle
                                if s1 in always2.get_sensList():
                                    # direct dependency
                                    self.builder[s1].add_child(self.builder[s2])
                                    self.builder[s2].add_parent(self.builder[s1])
                                else:
                                    # itercycle dependency
                                    self.builder[s1].add_inter_child(self.builder[s2])
                                    self.builder[s2].add_inter_parent(self.builder[s1])
                            # check opposite direction
                            if isinstance(s2, AssignStruct) and [i for i in s2.lhs_signals if i in s1.rhs_signals]:
                                # direct dependency
                                if s2 in always1.get_sensList():
                                    self.builder[s2].add_child(self.builder[s1])
                                    self.builder[s1].add_parent(self.builder[s2])
                                else:
                                    self.builder[s2].add_inter_child(self.builder[s1])
                                    self.builder[s1].add_inter_parent(self.builder[s2])
                        elif isinstance(s1, IfStruct):
                            if isinstance(s2, AssignStruct) and [i for i in s2.lhs_signals if i in s1.get_cond_dependencies()]:
                                if s2 in always1.get_sensList():
                                    self.builder[s2].add_child(self.builder[s1])
                                    self.builder[s1].add_parent(self.builder[s2])
                                else:
                                    self.builder[s2].add_inter_child(self.builder[s1])
                                    self.builder[s1].add_inter_parent(self.builder[s2])
        
        # connect coupling nodes
        for couple in self.coupling_nodes:
            # check assigns
            for a in self.signalvisitor.get_assigns():
                if [i for i in couple.outvars if i in a.rhs_signals]:
                    # dep from coupling to assignment
                    self.builder[a].add_parent(couple)
                    couple.add_child(self.builder[a])
                elif [i for i in couple.outvars if i in a.lhs_signals]:
                    #dep from assignment to coupling
                    self.builder[a].add_child(couple)
                    couple.add_parent(self.builder[a])
            for always in self.signalvisitor.get_always():
                for s in always.get_flattened_statements():
                    if isinstance(s, AssignStruct) and [i for i in couple.outvars if i in s.rhs_signals]:
                        # dep from coupling to assignment
                        self.builder[s].add_parent(couple)
                        couple.add_child(self.builder[s])
                    elif isinstance(s, AssignStruct) and [i for i in couple.outvars if i in s.lhs_signals]:
                        #dep from assignment to coupling
                        self.builder[s].add_child(couple)
                        couple.add_parent(self.builder[s])
                    elif (isinstance(s, IfStruct) or isinstance(s, CaseStatementStruct)) and [i for i in couple.outvars if i in s.get_cond_dependencies()]:
                         # dep from coupling to cond
                        self.builder[s].add_parent(couple)
                        couple.add_child(self.builder[s])
            for inp in self.signalvisitor.get_inputs():
                if inp in couple.outvars:
                    #dep from inp to couple
                        self.builder[inp].add_child(couple)
                        couple.add_parent(self.builder[inp])
            for out in self.signalvisitor.get_outputs():
                if out in couple.outvars:
                    #dep from couple to out
                        self.builder[out].add_parent(couple)
                        couple.add_child(self.builder[out])

    def clone(self):
        # foreach node clone and insert in a map
        # then fix arches
        node_map = {node: node.clone() for node in self.nodes}

        for node in self.nodes:
            if isinstance(node, CondNode):
                for child in node.true_statements:
                    node_map[node].add_child(node_map[child], True)
                for child in node.false_statements:
                    node_map[node].add_child(node_map[child], False)
            else:
                for child in node.get_children():
                    node_map[node].add_child(node_map[child])
            for parent in node.get_parents():
                node_map[node].add_parent(node_map[parent])
            for child in node.get_inter_children():
                node_map[node].add_inter_child(node_map[child])
            for parent in node.get_inter_parents():
                node_map[node].add_inter_parent(node_map[parent])
            for child in node.get_fictitious_children():
                node_map[node].add_fictitious_child(node_map[child])
            for parent in node.get_fictitious_parents():
                node_map[node].add_fictitious_parent(node_map[parent])
        return list(node_map.values())
    
    def connect_orphans(self):
        for node in self.nodes[1:]:
            if len(node.get_parents()) == 0 and len(node.get_inter_parents()) == 0 and len(node.get_fictitious_parents())== 0:
                # add fictitious edge
                node.add_fictitious_parent(self.nodes[0])
                self.nodes[0].add_fictitious_child(node)



def clone_nodelist(nodelist):
    node_map = {node: node.clone() for node in nodelist}

    for node in nodelist:
        for child in node.get_children():
            node_map[node].add_child(node_map[child])
        for parent in node.get_parents():
            node_map[node].add_parent(node_map[parent])
        for child in node.get_inter_children():
            node_map[node].add_inter_child(node_map[child])
        for parent in node.get_inter_parents():
            node_map[node].add_inter_parent(node_map[parent])
        for child in node.get_fictitious_children():
            node_map[node].add_fictitious_child(node_map[child])
        for parent in node.get_fictitious_parents():
            node_map[node].add_fictitious_parent(node_map[parent])
    return list(node_map.values())