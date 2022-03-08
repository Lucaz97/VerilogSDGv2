# -------------------------------------------------------------------------------
# signalvisitor.py
#
# Signal definition visitor
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

from pyverilog.vparser.ast import *
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
from SystemDependenceGraph.visit import *


class AssignStruct:
    def __init__(self, lhs_signals, rhs_signals, rhs_ast, rhs_consts):
        self.lhs_signals = lhs_signals
        self.rhs_signals = rhs_signals 
        self.rhs_consts = rhs_consts
        self.rhs_ast = rhs_ast

    def get_dependency_signals(self):
        signals = [s for s in self.rhs_signals]
        return signals

    def get_consts(self):
        return self.rhs_consts
 
    def __str__(self):
        rep = " ".join(self.lhs_signals) + "<-" + " ".join(self.rhs_signals)
        return rep


class BlockingAssignStruct(AssignStruct):
    pass

class NonBlockingAssignStruct(AssignStruct):
    pass


class AlwaysStruct:
    def __init__(self):
        self.statements = []
        self.sensitivityList = []

    def add_statement(self, statement):
        self.statements.append(statement)
    
    def set_sensList(self, sensList):
        self.sensitivityList = sensList

    def get_sensList(self):
        return self.sensitivityList

    def get_statements(self):
        return self.statements

    def get_flattened_statements(self):
        f_statements = []
        for s in self.statements:
            if isinstance(s,AssignStruct):
                f_statements.append(s)
            elif isinstance(s, IfStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
            elif isinstance(s, CaseStatementStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
        return f_statements
            
    def get_dependency_signals(self):
        deps = []
        for s in self.statements:
            deps.extend(s.get_dependency_signals())
        
        return list(set(deps))

    def __str__(self):
        rep = "ALWAYS" + "\nsensitivity list "+ ", ".join([str(s) for s in self.sensitivityList]) +"\n"
        rep +=  ", ".join([str(a) if a is not None else "" for a in self.statements]) +" END ALWAYS"
        return rep


class CaseStruct:
    def __init__(self):
        self.statements = []

    def get_statements(self):
        return self.statements

    def set_statements(self, statements):
        self.statements = statements

class CaseStatementStruct:
    def __init__(self):
        self.cond_signal = Node
        self.cases = []

    def set_cond_signal(self, cond_signal):
        self.cond_signal = cond_signal

    def get_cond_signal(self):
        return self.cond_signal

    def get_cases(self):
        return self.cases

    def get_n_cases(self):
        return len(self.cases)

    def add_case(self, case):
        self.cases.append(case)

    def get_cond_dependencies(self):
        return self.cond_signal

    def get_dependency_signals(self):
        signals = []
        for idx in self.cond_signal:
            signals.append(idx)
        for case in self.cases:
            for s in case.get_statements():
                for idx in s.get_dependency_signals():
                    signals.append(idx)
        return signals

    def get_flattened_statements(self):
        f_statements = [self]
        for case in self.cases:
            for s in case.get_statements():
                if isinstance(s,AssignStruct):
                    f_statements.append(s)
                elif isinstance(s, IfStruct):
                    for a in s.get_flattened_statements():
                        f_statements.append(a)
                elif isinstance(s, CaseStatementStruct):
                    for a in s.get_flattened_statements():
                        f_statements.append(a)
        return f_statements

class IfStruct:
    def __init__(self, arrays):
        self.cond = None
        self.trueStatements = []
        self.falseStatements =[]
        self.arrays = arrays
        self.ast = None

    def set_cond(self, cond):
        self.cond = cond

    def get_cond(self):
        return self.cond

    def set_trueStmts(self, stmts):
        self.trueStatements = stmts

    def get_trueStmts(self):
        return self.trueStatements
    
    def set_falseStmts(self, stmts):
        self.falseStatements = stmts

    def get_falseStmts(self):
        return self.falseStatements

    def get_dependency_signals(self):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(self.cond)
        signals = []
        for idx in iv.ids:
            signals.append(idx)
        for s in self.trueStatements+self.falseStatements:
            for idx in s.get_dependency_signals():
                signals.append(idx)
        return signals

    def get_cond_constants(self):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(self.cond)
        consts = []
        for c in iv.consts:
            consts.append(c)
        return consts

    def get_cond_dependencies(self):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(self.cond)
        signals = []
        for idx in iv.ids:
            signals.append(idx)
        return signals

    def get_flattened_statements(self):
        f_statements = [self]
        for s in self.trueStatements+self.falseStatements:
            if isinstance(s,AssignStruct):
                f_statements.append(s)
            elif isinstance(s, IfStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
            elif isinstance(s, CaseStatementStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
        return f_statements

    def get_true_flattened(self):
        f_statements = []
        for s in self.trueStatements:
            if isinstance(s,AssignStruct):
                f_statements.append(s)
            elif isinstance(s, IfStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
            elif isinstance(s, CaseStatementStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
        return f_statements

    def get_false_flattened(self):
        f_statements = []
        for s in self.falseStatements:
            if isinstance(s,AssignStruct):
                f_statements.append(s)
            elif isinstance(s, IfStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
            elif isinstance(s, CaseStatementStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
        return f_statements


    def __str__(self):
        rep = "IF " + (str(self.cond) if self.cond is not None else "") + " TRUE: " + " ".join([str(a) for a in self.trueStatements]) + " FALSE: " + " ".join([str(a) for a in self.falseStatements])
        return rep


class InstanceStruct:
    def __init__(self, module):
        self.module = module
        self.portlist = []

    def add_port(self, port):
        self.portlist.append(port)

    def get_module(self):
        return self.module

    def get_portlist(self):
        return self.portlist

    def __str__(self):
        return "INSTANCE " + self.module + " PORTS: " + " ".join([str(p) for p in self.portlist])

class InstanceVisitor(NodeVisitor):
    def __init__(self, node, arrays):
        self.struct = InstanceStruct(node.module)
        self.node = node
        self.arrays = arrays

    def start_visit(self):
        self.visit(self.node)

    def visit_PortArg(self, node):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(node.argname)
        self.struct.add_port((node.portname, iv.ids))

class IfVisitor(NodeVisitor):
    def __init__(self, arrays):
        self.statements = []
        self.arrays = arrays

    def visit_IfStatement(self,node):
        ifv_true = IfVisitor(self.arrays)
        if_struct = IfStruct(self.arrays)
        if_struct.set_cond(node.cond)
        if_struct.ast = node
        ifv_true.visit(node.true_statement)
        if_struct.set_trueStmts(ifv_true.statements)

        if node.false_statement != None: 
            ifv_false = IfVisitor(self.arrays)
            ifv_false.visit(node.false_statement)
            if_struct.set_falseStmts(ifv_false.statements)
        else:
            if_struct.set_falseStmts([])

        self.statements.append(if_struct)

    def visit_BlockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.statements.append(BlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_NonblockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.statements.append(NonBlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_CaseStatement(self, node):
        css = CaseStatementStruct()

        iv = IdentifierVisitor(self.arrays)
        iv.visit(node.comp)
        css.set_cond_signal(iv.ids)
        for case in node.caselist:
            cs = CaseStruct()
            cv = CaseVisitor(self.arrays)
            cv.visit(case.statement)
            cs.set_statements(cv.statements)
            css.add_case(cs)

        self.statements.append(css)


class CaseVisitor(NodeVisitor):
    def __init__(self, arrays):
        self.statements = []
        self.arrays = arrays

    def visit_IfStatement(self,node):
        ifv_true = IfVisitor(self.arrays)
        if_struct = IfStruct(self.arrays)
        if_struct.set_cond(node.cond)
        if_struct.ast = node
        ifv_true.visit(node.true_statement)
        if_struct.set_trueStmts(ifv_true.statements)

        if node.false_statement != None: 
            ifv_false = IfVisitor(self.arrays)
            ifv_false.visit(node.false_statement)
            if_struct.set_falseStmts(ifv_false.statements)
        else:
            if_struct.set_falseStmts([])

        self.statements.append(if_struct)

    def visit_BlockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.statements.append(BlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_NonblockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.statements.append(NonBlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_CaseStatement(self, node):
        css = CaseStatementStruct()

        iv = IdentifierVisitor(self.arrays)
        iv.visit(node.comp)
        css.set_cond_signal(iv.ids)
        for case in node.caselist:
            cs = CaseStruct()
            cv = CaseVisitor(self.arrays)
            cv.visit(case.statement)
            cs.set_statements(cv.statements)
            css.add_case(cs)

        self.statements.append(css)



class AlwaysVisitor(NodeVisitor):
    def __init__(self,arrays):
        self.struct =  AlwaysStruct()
        self.arrays = arrays

    def visit_SensList(self, node):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(node)
        self.struct.set_sensList(iv.ids)

    def visit_IfStatement(self,node):
        ifv_true = IfVisitor(self.arrays)
        if_struct = IfStruct(self.arrays)
        if_struct.set_cond(node.cond)
        if_struct.ast = node
        ifv_true.visit(node.true_statement)
        if_struct.set_trueStmts(ifv_true.statements)

        if node.false_statement != None: 
            ifv_false = IfVisitor(self.arrays)
            ifv_false.visit(node.false_statement)
            if_struct.set_falseStmts(ifv_false.statements)
        else:
            if_struct.set_falseStmts([])

        self.struct.add_statement(if_struct)

    def visit_CaseStatement(self, node):
        css = CaseStatementStruct()

        iv = IdentifierVisitor(self.arrays)
        iv.visit(node.comp)
        css.set_cond_signal(iv.ids)
        for case in node.caselist:
            cs = CaseStruct()
            cv = CaseVisitor(self.arrays)
            cv.visit(case.statement)
            cs.set_statements(cv.statements)
            css.add_case(cs)

        self.struct.add_statement(css)

    def visit_BlockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.struct.add_statement(BlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_NonblockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.struct.add_statement(NonBlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))


class IdentifierVisitor(NodeVisitor):
    def __init__(self, arrays):
        self.ids = []
        self.consts = []
        self.arrays = arrays

    def visit_Pointer(self, node):
        # if is pointer to an array, we consider it as a signal of its own
        # if is pointer to a signal we consider it as the signal
        if node.var.name in self.arrays:
            if isinstance(node.ptr, Constant):
                self.ids.append(node.var.name+"["+node.ptr.value+"]")
            elif isinstance(node.ptr, Partselect):
                self.ids.append(node.var.name+"["+node.ptr.var.name+"["+ node.ptr.msb.value+":"+node.ptr.lsb.value+"]]")
        else:
            self.generic_visit(node)

    def visit_Identifier(self, node):
        self.ids.append(node.name)

    def  visit_IntConst(self, node):
        self.consts.append(node)

    def  visit_FloatConst(self, node):
        self.consts.append(node)

    def  visit_StringConst(self, node):
        self.consts.append(node)

    def visit_Partselect(self, node):
        self.ids.append(node.var.name)



class FunctionStruct:
    def __init__(self):
        self.statements = []
        self.inputs = []

    def add_statement(self,s):
        self.statements.append(s)

    def add_input(self, i):
        self.inputs.append(i)

    def get_inputs(self):
        return self.inputs

    def get_statements(self):
        return self.statements

    def get_flattened_statements(self):
        f_statements = []
        for s in self.statements:
            if isinstance(s,AssignStruct):
                f_statements.append(s)
            elif isinstance(s, IfStruct):
                f_statements.append(s)
                for a in s.get_flattened_statements():
                    f_statements.append(a)
            elif isinstance(s, CaseStatementStruct):
                for a in s.get_flattened_statements():
                    f_statements.append(a)
        return f_statements
            
    def get_dependency_signals(self):
        return [s.get_dependency_signals() for s in self.statements]


class FunctionVisitor(NodeVisitor):
    
    def __init__(self, node, arrays):
        self.node = node
        self.arrays = arrays
        self.struct = FunctionStruct()
        self.visit(node)
        self.name = node.name
    
    def visit_IfStatement(self,node):
        ifv_true = IfVisitor(self.arrays)
        if_struct = IfStruct(self.arrays)
        if_struct.set_cond(node.cond)
        if_struct.ast = node
        ifv_true.visit(node.true_statement)
        if_struct.set_trueStmts(ifv_true.statements)

        if node.false_statement != None: 
            ifv_false = IfVisitor(self.arrays)
            ifv_false.visit(node.false_statement)
            if_struct.set_falseStmts(ifv_false.statements)
        else:
            if_struct.set_falseStmts([])

        self.struct.add_statement(if_struct)

    def visit_CaseStatement(self, node):
        css = CaseStatementStruct()

        iv = IdentifierVisitor(self.arrays)
        iv.visit(node.comp)
        css.set_cond_signal(iv.ids)
        for case in node.caselist:
            cs = CaseStruct()
            cv = CaseVisitor(self.arrays)
            cv.visit(case.statement)
            cs.set_statements(cv.statements)
            css.add_case(cs)

        self.struct.add_statement(css)

    def visit_BlockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.struct.add_statement(BlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_NonblockingSubstitution(self, node):
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.struct.add_statement(NonBlockingAssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    def visit_Input(self, node):
        self.struct.add_input(node.name)
    

class SignalVisitor(NodeVisitor):
    def __init__(self, arrays):
        self.assigns = []
        self.always = []
        self.instances = []
        self.inputs = []
        self.outputs = []
        self.parameters = []
        self.functions = []
        self.arrays = arrays

    def visit_Assign(self, node):
        # I need to store lhs signal, rhs signals
        ivlhs = IdentifierVisitor(self.arrays)
        ivlhs.visit(node.left)
        
        ivrhs = IdentifierVisitor(self.arrays)
        ivrhs.visit(node.right)
        
        self.assigns.append(AssignStruct(ivlhs.ids, ivrhs.ids, node.right, ivrhs.consts))

    # Always:  (at 279)
    #     SensList:  (at 279)
    #       Sens: posedge (at 279)
    #         Identifier: clk (at 279)
    #       Sens: negedge (at 279)
    #         Identifier: reset (at 279)
    #     Block: None (at 279)
    #       IfStatement:  (at 280)
    #         Unot:  (at 280)
    #           Identifier: reset (at 280)
    #         Block: None (at 280)
    #           NonblockingSubstitution:  (at 281)
    #             Lvalue:  (at 281)
    #               Identifier: outData (at 281)
    #             Rvalue:  (at 281)
    #               IntConst: 32'h00000000, 281 (at 281)
    #         Block: None (at 282)
    #           NonblockingSubstitution:  (at 283)
    #             Lvalue:  (at 283)
    #               Identifier: outData (at 283)
    #             Rvalue:  (at 283)
    #               Identifier: outData_in (at 283)

    def visit_Always(self, node):
        av = AlwaysVisitor(self.arrays)
        av.visit(node)
        if len(av.struct.get_sensList()) == 0:
            av.struct.set_sensList(av.struct.get_dependency_signals())
        self.always.append(av.struct)

    def visit_Instance(self, node):
        #Instance: my_FIR_filter_firBlock_right_MultiplyBlock, FIR_filter_firBlock_right_MultiplyBlock (at 238)
        #  PortArg: X (at 239)
        #    Identifier: X (at 239)
        #  PortArg: Y (at 240)
        #    Identifier: multProducts (at 240)
        inst_visitor = InstanceVisitor(node, self.arrays)
        inst_visitor.start_visit()
        self.instances.append(inst_visitor.struct)

    def visit_Input(self, node):
        self.inputs.append(node.name)

    def visit_Output(self, node):
        self.outputs.append(node.name)

    def visit_Parameter(self, node):
        iv = IdentifierVisitor(self.arrays)
        iv.visit(node)

        self.parameters.append(ParameterStruct(node.name, iv.ids, iv.consts))

    # def visit_Function(self, node):
    #     fv = FunctionVisiter(node, self.arrays)
    #     self.function.append(fv.struct)

    def get_assigns(self):
        return self.assigns

    def get_instances(self):
        return self.instances

    def get_always(self):
        return self.always
    
    def get_inputs(self):
        return self.inputs
    
    def get_outputs(self):
        return self.outputs

    def get_parameters(self):
        return self.parameters

    def get_functions(self):
        return self.functions

class ParameterStruct:
    def __init__(self, name, ids, consts):
        self.name = name
        self.ids = ids
        self.consts = consts

    def get_name(self):
        return self.name
    
    def get_ids(self):
        return self.ids

    def get_consts(self):
        return self.consts