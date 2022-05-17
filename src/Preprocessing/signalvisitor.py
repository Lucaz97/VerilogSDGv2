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
from operator import mod
import sys
from webbrowser import Opera

from pyverilog.vparser.ast import *
from SystemDependenceGraph.visit import *

def get_width(lut, lhs):
    # lut is width, dimensions
    if isinstance(lhs, Lvalue):
        lhs = lhs.var
    if isinstance(lhs, LConcat):
        w = 0
        for c in lhs.list:
            w += get_width(lut, c)
    elif isinstance(lhs, Pointer):
        if lut[lhs.var.name][1]:
            if isinstance(lut[lhs.var.name][0].msb, Operator) or isinstance(lut[lhs.var.name][0].msb, Operator) or isinstance(lut[lhs.var.name][0].msb, Identifier) or isinstance(lut[lhs.var.name][0].msb, Identifier):
                w = lut[lhs.var.name][0]
            else:
                w = int(lut[lhs.var.name][0].msb.value) - int(lut[lhs.var.name][0].lsb.value) + 1
        else:    
            w = 1
    elif isinstance(lhs, Partselect):
        w = int(lhs.msb.value) - int(lhs.lsb.value) + 1
    elif lhs.name not in lut:
            w = 1
    elif lut[lhs.name][0]:
        if isinstance(lut[lhs.name][0].msb, Operator) or isinstance(lut[lhs.name][0].msb, Operator) or isinstance(lut[lhs.name][0].msb, Identifier) or isinstance(lut[lhs.name][0].msb, Identifier):
            w = lut[lhs.name][0]
        else:
            w = int(lut[lhs.name][0].msb.value) - int(lut[lhs.name][0].lsb.value) + 1
    else:
        w = 1
    return w


class IfCondVisitor(NodeVisitor):
    def __init__(self, module, dwv):
        self.new_decls = []
        self.module = module
        self.dwv = dwv

    def visit_Block(self, node):
        bv = BlockIfVisitor(node, self.module, self.dwv)
        bv.generic_visit(node)
        if bv.new_decls:
            for nd in bv.new_decls:
                    new_decl = Decl([Reg(nd.name)])
                    temp_list = list(self.module.items)
                    temp_list.insert(0, new_decl)
                    self.module.items = tuple(temp_list)
class BlockIfVisitor(NodeVisitor):
    
    def __init__(self, node, module, dwv):
        self.node = node
        self.new_decls = []
        self.module = module
        self.dwv = dwv

    def visit_Block(self, node):
        bv = BlockIfVisitor(node, self.module, self.dwv)
        bv.generic_visit(node)
        if bv.new_decls:
            for nd in bv.new_decls:
                    new_decl = Decl([Reg(nd.name)])
                    temp_list = list(self.module.items)
                    temp_list.insert(0, new_decl)
                    self.module.items = tuple(temp_list)

    def visit_IfStatement(self, node):
        cond = node.cond
        extracted_id = Identifier("COND_"+cond.__class__.__name__ + '_' + str(id(cond)))
        new_assign = BlockingSubstitution(Lvalue(extracted_id), Rvalue(cond))
        i = self.node.statements.index(node)
        temp_list = list(self.node.statements)
        temp_list.insert(i,new_assign)
        self.node.statements = tuple(temp_list)
        node.cond = extracted_id
        self.new_decls.append(extracted_id)
        self.visit(node.true_statement)
        if node.false_statement:
            self.visit(node.false_statement)

class BlockVisitor(NodeVisitor):
    def __init__(self, node, module, dwv):
        self.node = node
        self.new_decls = []
        self.module = module
        self.dwv = dwv

    def visit_Block(self, node):
        bv = BlockVisitor(node, self.module, self.dwv)
        bv.generic_visit(node)
        if bv.new_decls:
            for nd in bv.new_decls:
                w = get_width( self.dwv.signaltable, nd[0])
                if not isinstance(w, Width):
                    w = Width(IntConst(w-1), IntConst(0))
                for s in nd[1]:
                    new_decl = Decl([Reg(s.name, width=w)])
                    temp_list = list(self.module.items)
                    temp_list.insert(0, new_decl)
                    self.module.items = tuple(temp_list)

    def visit_ForStatement(self, node):
        self.visit(node.statement)

    def visit_BlockingSubstitution(self, node):
        rhsv = RHSVisitor(True)
        rhsv.visit(node.right)

        if rhsv.extracted_ID:
            if node not in self.node.statements:
                print("ERROR: node not in block\n", self.node.statements, "\n", node, node.lineno, file=sys.stderr)
            i = self.node.statements.index(node)
            node.right = Rvalue(Identifier(rhsv.extracted_ID.name))
            temp_list = list(self.node.statements)
            for s in reversed(rhsv.expanded_statements):
                temp_list.insert(i,s)
            self.node.statements = tuple(temp_list)
            self.new_decls.append((node.left, rhsv.new_decls))

    def visit_NonblockingSubstitution(self, node):
        rhsv = RHSVisitor(False)
        rhsv.visit(node.right)

        if rhsv.extracted_ID:
            i = self.node.statements.index(node)
            node.right = Rvalue(Identifier(rhsv.extracted_ID.name))
            # for non blocking I need a new comb block.
            statment_list = []
            for s in reversed(rhsv.expanded_statements):
                statment_list.insert(i,s)
            
            new_always = Always(SensList([Sens(None, 'all')]), Block(statment_list))
            
            temp_list = list(self.module.items)
            temp_list.append(new_always)
            self.module.items = tuple(temp_list)
            self.new_decls.append((node.left, rhsv.new_decls))
        


class IdentifierVisitor(NodeVisitor):
    def __init__(self, ):
        self.ids = []
        self.consts = []

    def visit_Pointer(self, node):
        self.ids.append(node)

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

class RHSVisitor(NodeVisitor):
    
    def __init__(self, blocking):
        self.expanded_statements = []
        self.new_decls = []
        self.blocking = blocking
        self.extracted_ID = None

    # Method for binary operators
    def visit_Repeat(self, node):
        pass
    def visit_Concat(self, node):
        pass
    def visit_BinOp(self, node): 
        #print(node)
        # look left
        if isinstance(node.left, (Identifier, Pointer, Partselect, Value, Concat, FunctionCall)):
            left = node.left
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.left)
            print(node)
            print(node.left)
            left = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        # look right
        if isinstance(node.right, (Identifier, Pointer, Partselect, Value, Concat, FunctionCall)):
            right = node.right
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.right)
            right = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        new_op =  node.__class__(left, right)
        self.extracted_ID = Identifier(node.__class__.__name__ + '_' + str(id(node)))
        if self.blocking:
            new_assign = BlockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        else:
            new_assign = NonblockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        
        self.expanded_statements.append(new_assign)
        self.new_decls.append(self.extracted_ID)

    def visit_Power(self, node):
        self.visit_BinOp(node)

    def visit_Times(self, node):
        self.visit_BinOp(node)

    def visit_Divide(self, node):
        self.visit_BinOp(node)

    def visit_Mod(self, node):
        self.visit_BinOp(node)

    # Level 3
    def visit_Plus(self, node):
        self.visit_BinOp(node)

    def visit_Minus(self, node):
        self.visit_BinOp(node)

    # Level 4
    def visit_Sll(self, node):
        self.visit_BinOp(node)

    def visit_Srl(self, node):
        self.visit_BinOp(node)

    def visit_Sla(self, node):
        self.visit_BinOp(node)

    def visit_Sra(self, node):
        self.visit_BinOp(node)

    # Level 5
    def visit_LessThan(self, node):
        self.visit_BinOp(node)

    def visit_GreaterThan(self, node):
        self.visit_BinOp(node)

    def visit_LessEq(self, node):
        self.visit_BinOp(node)

    def visit_GreaterEq(self, node):
        self.visit_BinOp(node)

    # Level 6
    def visit_Eq(self, node):
        self.visit_BinOp(node)

    def visit_NotEq(self, node):
        self.visit_BinOp(node)

    def visit_Eql(self, node):
        self.visit_BinOp(node)  # ===

    def visit_NotEql(self, node):
        self.visit_BinOp(node)  # !==

    # Level 7
    def visit_And(self, node):
        self.visit_BinOp(node)

    def visit_Xor(self, node):
        self.visit_BinOp(node)

    def visit_Xnor(self, node):
        self.visit_BinOp(node)

    # Level 8
    def visit_Or(self, node):
        self.visit_BinOp(node)

    # Level 9
    def visit_Land(self, node):
        self.visit_BinOp(node)

    # Level 10
    def visit_Lor(self, node):
        self.visit_BinOp(node)

    
######################################################
    # Unary operators
    def visit_UnOp(self, node):
        #print(node)
        if isinstance(node.right, (Identifier, Pointer, Partselect, Value)):
            right = node.right
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.right)
            right = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        new_op =  node.__class__( right)
        self.extracted_ID = Identifier(node.__class__.__name__ + '_' + str(id(node)))
        if self.blocking:
            new_assign = BlockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        else:
            new_assign = NonblockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        self.expanded_statements.append(new_assign)
        self.new_decls.append(self.extracted_ID)

    def visit_Uplus(self, node):
        self.visit_UnOp(node)

    def visit_Uminus(self, node):
        self.visit_UnOp(node)

    def visit_Ulnot(self, node):
        self.visit_UnOp(node)

    def visit_Unot(self, node):
        self.visit_UnOp(node)

    def visit_Uand(self, node):
        self.visit_UnOp(node)

    def visit_Unand(self, node):
        self.visit_UnOp(node)

    def visit_Uor(self, node):
        self.visit_UnOp(node)

    def visit_Unor(self, node):
        self.visit_UnOp(node)

    def visit_Uxor(self, node):
        self.visit_UnOp(node)

    def visit_Uxnor(self, node):
        self.visit_UnOp(node)

    def visit_Cond(self, node):
        if isinstance(node.true_value, (Identifier, Pointer, Partselect, Value)):
            true_value = node.true_value
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.true_value)
            true_value = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)
        
        if isinstance(node.false_value, (Identifier, Pointer, Partselect, Value)):
            false_value = node.false_value
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.false_value)
            false_value = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        self.extracted_ID = Identifier(node.__class__.__name__ + '_' + str(id(node)))
        if self.blocking:
            true_assign = BlockingSubstitution(Lvalue(self.extracted_ID), Rvalue(true_value))
            false_assign = BlockingSubstitution(Lvalue(self.extracted_ID), Rvalue(false_value))
        else:
            true_assign = NonblockingSubstitution(Lvalue(self.extracted_ID), Rvalue(true_value))
            false_assign = NonblockingSubstitution(Lvalue(self.extracted_ID), Rvalue(false_value))
        new_if_statement = IfStatement(node.cond, Block([true_assign]), Block([false_assign]))
        self.expanded_statements.append(new_if_statement)
        self.new_decls.append(self.extracted_ID)

class BinaryOpsVisitor(NodeVisitor):

    def __init__(self, module):
        self.module = module
        # identify inouts
        iov = InOutVisitor()
        iov.visit(module)

        # build datawidth table
        self.dwv = DatawidthVisitor()
        self.dwv.visit(module)

        # preprocess begin ends and assigns
        mbev = MissignBeginEndVisitor(module, iov.inouts, self.dwv)
        mbev.visit(module)
        mbev.fix_decls()
        
        icv = IfCondVisitor(module, self.dwv)
        icv.visit(module)

    #def visit_Assign(self, node):
    #    print("ERROR: continuous assigns not supported, run preprocessor!")
    #    quit()

    def visit_Block(self, node):
        bv = BlockVisitor(node, self.module, self.dwv)
        # check if new decls to add:
        bv.generic_visit(node)
        #print(bv.new_decls)
        if bv.new_decls:
            for nd in bv.new_decls:
                # nd is (lhs, list_of_new_var_names)
                w = get_width( self.dwv.signaltable, nd[0])
                if not isinstance(w, Width):
                    w = Width(IntConst(w-1), IntConst(0))
                for s in nd[1]:
                    new_decl = Decl([Reg(s.name, width=w)])
                    temp_list = list(self.module.items)
                    temp_list.insert(0, new_decl)
                    self.module.items = tuple(temp_list)

class DatawidthVisitor(NodeVisitor):
    def __init__(self):
        self.signaltable={}

    def addEntry(self, name, width, dimensions):
        if name not in self.signaltable or self.signaltable[name] == None:
            self.signaltable[name] = (width, dimensions)

    def visit_Input(self, node):
        self.addEntry(node.name, node.width, node.dimensions)

    def visit_Output(self, node):
        self.addEntry(node.name, node.width, node.dimensions)
    
    def visit_Inout(self, node):
        self.addEntry(node.name, node.width, node.dimensions)

    def visit_Reg(self, node):
        self.addEntry(node.name, node.width, node.dimensions)
    def visit_Wire(self, node):
        self.addEntry(node.name, node.width, node.dimensions)
    
    def visit_IntConst(self,node):
        if "'" in node.value:
            width = Width(IntConst(int(node.value.split("'")[0])-1), IntConst(0))
        else:
            width = Width(IntConst(31), IntConst(0))
        self.addEntry(node, width, None)


class MissignBeginEndVisitor(NodeVisitor):        
    
    def __init__(self, module,inouts,dwv):
        self.module = module
        self.to_fix = []
        self.decls = []
        self.inouts = inouts
        self.dwv = dwv

    def visit_Decl(self, node): 
        self.decls.append(node)

    def visit_Always(self, node):
        if not isinstance(node.statement, Block):
            new_block = Block([node.statement])
            node.statement = new_block
        self.generic_visit(node)

    def visit_ForStatement(self, node): 
        if not isinstance(node.statement, Block):
            new_block = Block([node.statement])
            node.statement = new_block
        self.generic_visit(node)
    
    def visit_IfStatement(self, node):
        if not isinstance(node.true_statement, Block):
            new_block = Block([node.true_statement])
            node.true_statement = new_block
        if node.false_statement and not isinstance(node.false_statement, Block):
            new_block = Block([node.false_statement])
            node.false_statement = new_block
        self.generic_visit(node)
    
    def visit_Case(self, node):
        if not isinstance(node.statement, Block):
            new_block = Block([node.statement])
            node.statement = new_block
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.right.var, Operator):

            iv = _IdentifierVisitor()
            iv.visit(node.left)
            any_inouts = False
            for idf in iv.ids:
                if idf in self.inouts:
                    any_inouts = True
                    break
            if any_inouts:
                extracted_id = Identifier(node.__class__.__name__ + '_' + str(id(node)))
                new_blockingSub = BlockingSubstitution(Lvalue(extracted_id),node.right)
                new_always = Always(SensList([Sens(None, 'all')]), Block([new_blockingSub]))
                temp_list = list(self.module.items)
                node.right = Rvalue(extracted_id)
                temp_list.append(new_always)
                self.to_fix.append(node.left)
                self.module.items = tuple(temp_list)
                w = get_width( self.dwv.signaltable, node.left)
                if not isinstance(w, Width):
                    w = Width(IntConst(w-1), IntConst(0))
                new_decl = Decl([Reg(extracted_id.name, width=w)])
                temp_list = list(self.module.items)
                temp_list.insert(0, new_decl)
                self.module.items = tuple(temp_list)
            else:
                new_blockingSub = BlockingSubstitution(node.left,node.right)
                new_always = Always(SensList([Sens(None, 'all')]), Block([new_blockingSub]))
                temp_list = list(self.module.items)
                temp_list.remove(node)
                temp_list.append(new_always)
                self.to_fix.append(node.left)
                self.module.items = tuple(temp_list)

    def fix_decls(self):
        print(self.to_fix)
        for lhs in self.to_fix:
            iv = _IdentifierVisitor()
            iv.visit(lhs)
            for l in self.decls:
                temp_list = list(l.list)
                for i, d in enumerate(l.list):
                    if isinstance(d, Output) and (len(l.list) <= i+1 or isinstance(l.list[i+1], Output)) and d.name in iv.ids:
                        # this is for when you just have output without reg or wire
                        new_reg = Reg(d.name, width=d.width, dimensions=d.dimensions, signed=d.signed, lineno=d.lineno)
                        temp_list.append(new_reg)
                    elif isinstance(d, Wire) and d.name in iv.ids:
                        # gotta change decl from Wire to Reg
                        new_reg = Reg(d.name, width=d.width, dimensions=d.dimensions, signed=d.signed, lineno=d.lineno)
                        temp_list.remove(d)
                        temp_list.append(new_reg)
                l.list = temp_list
            for p in self.module.portlist.ports:
                 if isinstance(p, Ioport) and not p.second and isinstance(p.first, Output) and p.first.name in iv.ids:
                    new_reg = Reg(p.first.name, width=p.first.width, dimensions=p.first.dimensions, signed=p.first.signed, lineno=p.first.lineno)
                    p.second = new_reg
                 elif isinstance(p, Ioport) and p.second and isinstance(p.second, Wire) and p.second.name in iv.ids:
                    new_reg = Reg(p.second.name, width=p.second.width, dimensions=p.second.dimensions, signed=p.second.signed, lineno=p.second.lineno)
                    p.second = new_reg


class InOutVisitor(NodeVisitor):
    def __init__(self):
        self.inouts = []
    
    def visit_Inout(self, node):
        self.inouts.append(node.name)

class _IdentifierVisitor(NodeVisitor):
            def __init__(self): 
                self.ids = []
            
            def visit_Identifier(self, node): 
                self.ids.append(node.name)
                #print("ID:",node.name)