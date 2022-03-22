
from SystemDependenceGraph.visit import *
from SystemDependenceGraph.signalvisitor import *
from SystemDependenceGraph.DependenceNode import *
from SystemDependenceGraph.Graph import *
import traceback
class ProgramDependencyGraph(Graph):
    
    def __init__(self, parent_node):
        super().__init__()
        self.parent_node = parent_node
        if isinstance(parent_node, AlwaysStruct):
            self._add_alwaysNode(parent_node)
        elif isinstance(parent_node, FunctionStruct):
            self._add_functionNode(parent_node)

    def _add_alwaysNode(self, always):
        anode = AlwaysNode(always.get_sensList())
        self.nodes.append(anode)
        self.builder[always] = anode

    # def _add_alwaysNode(self, function):
    #     fnode = FunctionNode() #TODO FIX THIS ONCE FunctionNode implemented
    #     self.nodes.append(fnode)
    #     self.builder[always] = fnode

    def build(self):
        self.build_nodes(self.parent_node.get_statements())
        self.build_edges(self.parent_node.get_statements())
        self.connect_orphans()

    def build_nodes(self, statements):
        for statement in statements:
            if isinstance(statement, AssignStruct):
                node = AssignNode(str(statement))
                node.set_ast(statement.rhs_ast)
                self.nodes.append(node)
                self.builder[statement] = node
                for c in statement.get_consts():
                    const_node = ConstNode(c)
                    self.nodes.append(const_node)
                    const_node.add_child(node)
                    node.add_parent(const_node)
            elif isinstance(statement, IfStruct):
                # create condition node
                cnode = CondNode(statement)
                cnode.set_ast(statement.ast)
                self.nodes.append(cnode)
                self.builder[statement] = cnode

                # create const nodes
                for c in statement.get_cond_constants():    
                    const_node = ConstNode(c)
                    self.nodes.append(const_node)
                    const_node.add_child(cnode)
                    cnode.add_parent(const_node)

                # create true statements nodes 
                self.build_nodes(statement.get_trueStmts())
                # connect condition to statements 
                for s in statement.get_trueStmts():
                    cnode.add_child(self.builder[s],True)
                    self.builder[s].add_parent(cnode)
                # create false statements nodes 
                self.build_nodes(statement.get_falseStmts())
                # connect
                for s in statement.get_falseStmts():
                    cnode.add_child(self.builder[s], False)
                    self.builder[s].add_parent(cnode)
            elif isinstance(statement, CaseStatementStruct):
                # create condition node
                cnode = CondNode(statement)
                cnode.set_ast(statement.get_cond_signal())
                self.nodes.append(cnode)
                self.builder[statement] = cnode

                # create case statements nodes 
                for case in statement.get_cases():
                    self.build_nodes(case.get_statements())
                    
                # connect condition to statements 
                for case in statement.get_cases():
                    for s in case.get_statements():
                        cnode.add_child(self.builder[s], None)
                        self.builder[s].add_parent(cnode)


    def build_edges(self, statements):
        # cond nodes are already connected

        for i,statement in enumerate(statements):
            # for each nonblocking assign easy: check if lhs is in rhs or in condition
            # TODO FIX current solution misses if  true and false statements CHECK BELOW
            if isinstance(statement, NonBlockingAssignStruct):
                for s in self.parent_node.get_flattened_statements(): # THIS SHOULD BE THE FIX AS FOR NON BLOCKING I DONT CARE ABOUT THE ORDER AND EACH STMT MUST BE COMPARED AGAINST EACH OTHER STATEMENT
                    if s != statement:
                        if (isinstance(s, AssignStruct) and [i for i in statement.lhs_signals if i in s.rhs_signals]) or (isinstance(s, IfStruct) and [i for i in statement.lhs_signals if i in s.get_cond_dependencies()]) :
                            # s depends on statement
                            self.builder[statement].add_inter_child(self.builder[s])
                            self.builder[s].add_inter_parent(self.builder[statement])
            # WRONG: 
            # # I DONT REMEMBER WHY I COMMENTED WRONG HERE, IT SEEMS FINE
            # OK MAYBE IS BECAUSE I LOSE STUFF, I NEED TO CHECK BELOW HOW I DID FOR BLOCKING CASES
            # I think this is necessary but i need to fix above and to add case below
            elif isinstance(statement, IfStruct):
                self.build_edges(statement.get_trueStmts()+statements[i+1:])
                self.build_edges(statement.get_falseStmts()+statements[i+1:])
            elif isinstance(statement, CaseStatementStruct):
                for case in statement.get_cases():
                    self.build_edges(case.get_statements()+statements[i+1:])

            # for blocking assignments i only check the following statements
            # check direct dependencies:
            elif isinstance(statement, BlockingAssignStruct):
                for lhs in statement.lhs_signals:
                    parent_nodes = [self.builder[statement]] # parent nodes is a list because when branching we may get more than one parent
                    for s in statements[i+1:]:
                        if isinstance(s, BlockingAssignStruct): 
                            if lhs in s.lhs_signals:
                                parent_nodes = [self.builder[s]]
                            if lhs in s.rhs_signals:
                                # dependency 
                                for pn in parent_nodes:
                                    pn.add_child(self.builder[s])
                                    self.builder[s].add_parent(pn)
                        if isinstance(s, IfStruct):
                            parent_nodes = self.check_if_blocking(s, parent_nodes, lhs)
                        if isinstance(s, CaseStatementStruct):
                            parent_nodes = self.check_case_statement_blocking(s, parent_nodes, lhs)

    def check_if_blocking(self, statement, parent_nodes, lhs):
        # check dependency of condition
        if lhs in statement.get_cond_dependencies():
            for pn in parent_nodes:
                pn.add_child(self.builder[statement])
                self.builder[statement].add_parent(pn)
        
        #flag for 
        found_true = 0
        for s in statement.get_trueStmts():
            if isinstance(s, BlockingAssignStruct): 
                if lhs in s.lhs_signals:
                    tmp_true_parent_nodes = [self.builder[s]]
                    found_true = 1
                if lhs in s.rhs_signals:
                    # dependency 
                    for pn in parent_nodes if found_true == 0 else tmp_true_parent_nodes:
                        pn.add_child(self.builder[s])
                        self.builder[s].add_parent(pn)
            if isinstance(s, IfStruct):
                tmp_true_parent_nodes = self.check_if_blocking(s, parent_nodes if found_true == 0 else tmp_true_parent_nodes, lhs)
                if tmp_true_parent_nodes != parent_nodes:
                    found_true = 1
            if isinstance(s, CaseStatementStruct):
                tmp_true_parent_nodes = self.check_case_statement_blocking(s, parent_nodes if found_true == 0 else tmp_true_parent_nodes, lhs)
                if tmp_true_parent_nodes != parent_nodes:
                    found_true = 1
        found_false = 0
        for s in statement.get_falseStmts():
            if isinstance(s, BlockingAssignStruct): 
                if lhs in s.lhs_signals:
                    tmp_false_parent_nodes = [self.builder[s]]
                    found_false = 1
                if lhs in s.rhs_signals:
                    # dependency 
                    for pn in parent_nodes if found_false == 0 else tmp_false_parent_nodes:
                        pn.add_child(self.builder[s])
                        self.builder[s].add_parent(pn)
            if isinstance(s, IfStruct):
                tmp_false_parent_nodes = self.check_if_blocking(s, parent_nodes if found_false == 0 else tmp_false_parent_nodes, lhs)
                if tmp_false_parent_nodes != parent_nodes:
                    found_false = 1
            if isinstance(s, CaseStatementStruct):
                tmp_false_parent_nodes = self.check_case_statement_blocking(s, parent_nodes if found_false == 0 else tmp_false_parent_nodes, lhs)
                if tmp_false_parent_nodes != parent_nodes:
                    found_false = 1

        if found_true + found_false == 2:
            #found in both branches -> parent nodes are union(tmp_true_parent_nodes and tmp_false_parent_nodes)
            return tmp_true_parent_nodes + tmp_false_parent_nodes
        elif found_true == 1:
            return parent_nodes + tmp_true_parent_nodes
        elif found_false == 1:
            return parent_nodes + tmp_false_parent_nodes
        else:
            return parent_nodes
            
    def check_case_statement_blocking(self, statement, parent_nodes, lhs):
        # check dependency of condition
        if lhs in statement.get_cond_dependencies():
            for pn in parent_nodes:
                pn.add_child(self.builder[statement])
                self.builder[statement].add_parent(pn)
        
        #flag for 
        found_true = 0
        tmp_parent_nodes = []
        for i, case in enumerate(statement.get_cases()):
            tmp_parent_nodes.append([])
            for s in case.get_statements():
                if isinstance(s, BlockingAssignStruct): 
                    if lhs in s.lhs_signals:
                        tmp_parent_nodes[i] = [self.builder[s]]
                        found_true += 1
                    if lhs in s.rhs_signals:
                        # dependency 
                        for pn in parent_nodes if len(tmp_parent_nodes[i]) == 0 else tmp_parent_nodes[i]:
                            pn.add_child(self.builder[s])
                            self.builder[s].add_parent(pn)
                if isinstance(s, IfStruct):
                    if len(tmp_parent_nodes[i]) == 0:
                        tmp_parent_nodes[i] = self.check_if_blocking(s, parent_nodes, lhs)
                    else:
                        tmp_parent_nodes[i] = self.check_if_blocking(s, tmp_parent_nodes[i], lhs)   
                    if tmp_parent_nodes[i] != parent_nodes:
                        found_true += 1
                if isinstance(s, CaseStatementStruct):
                    tmp_parent_nodes[i] = self.check_case_statement_blocking(s, parent_nodes if len(tmp_parent_nodes[i]) == 0 else tmp_parent_nodes[i], lhs)
                    if tmp_parent_nodes[i] != parent_nodes:
                        found_true += 1
   
        if found_true == statement.get_n_cases():
            #found in both branches -> parent nodes are union(tmp_true_parent_nodes and tmp_false_parent_nodes)
            return [pn for sublist in tmp_parent_nodes for pn in sublist]
        else:
            return parent_nodes+[pn for sublist in tmp_parent_nodes for pn in sublist]

    def get_nodes(self):
        return self.nodes

    def get_builder(self):
        return self.builder

    def connect_orphans(self):
        for node in self.nodes[1:]:
            if len(node.get_parents()) == 0 and len(node.get_inter_parents()) == 0 and len(node.get_fictitious_parents())== 0:
                # add fictitious edge
                node.add_fictitious_parent(self.nodes[0])
                self.nodes[0].add_fictitious_child(node)
