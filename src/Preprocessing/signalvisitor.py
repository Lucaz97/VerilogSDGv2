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
from platform import node
import sys
import os

from pyverilog.vparser.ast import *
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
from SystemDependenceGraph.visit import *


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
                # nd is (new_id, left, right)
                # for now go easy and just copy left one and see how it goes
                #print(self.dwv.signaltable)
                #print(nd)
                if isinstance(nd[1], IntConst):
                    w = self.dwv.signaltable[nd[1]]
                else:
                    w = self.dwv.signaltable[nd[1].name]
                new_decl = Decl([Wire(nd[0].name, width=w)])
                temp_list = list(self.module.items)
                temp_list.append(new_decl)
                self.module.items = tuple(temp_list)
                self.dwv.addEntry(nd[0].name, w)

    def visit_BlockingSubstitution(self, node):
        rhsv = RHSVisitor(True)
        rhsv.visit(node.right)

        if rhsv.extracted_ID:
            i = self.node.statements.index(node)
            node.right = Rvalue(Identifier(rhsv.extracted_ID.name))
            temp_list = list(self.node.statements)
            for s in reversed(rhsv.expanded_statements):
                temp_list.insert(i,s)
            self.node.statements = tuple(temp_list)
            self.new_decls.extend(rhsv.new_decls)

    def visit_NonblockingSubstitution(self, node):
        rhsv = RHSVisitor(False)
        rhsv.visit(node.right)

        if rhsv.extracted_ID:
            i = self.node.statements.index(node)
            node.right = Rvalue(Identifier(rhsv.extracted_ID.name))
            temp_list = list(self.node.statements)
            for s in reversed(rhsv.expanded_statements):
                temp_list.insert(i,s)
            self.node.statements = tuple(temp_list)
            self.new_decls.extend(rhsv.new_decls)
        


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
    def visit_BinOp(self, node): 
        #print(node)
        # look left
        if isinstance(node.left, (Identifier, Pointer, Partselect, Value)):
            left = node.left
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.left)
            left = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        # look right
        if isinstance(node.right, (Identifier, Pointer, Partselect, Value)):
            right = node.right
        else:
            rhsv = RHSVisitor(self.blocking)
            rhsv.visit(node.right)
            right = Identifier(rhsv.extracted_ID.name)
            self.expanded_statements.extend(rhsv.expanded_statements)
            self.new_decls.extend(rhsv.new_decls)

        new_op =  node.__class__(left, right)
        self.extracted_ID = Identifier(node.__class__.__name__ + '_' + str(id(self)))
        if self.blocking:
            new_assign = BlockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        else:
            new_assign = NonblockingSubstitution(Lvalue(self.extracted_ID), Rvalue(new_op))
        
        self.expanded_statements.append(new_assign)
        self.new_decls.append((self.extracted_ID, left, right))

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
        self.new_decls.append((self.extracted_ID, right, right))

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
        self.new_decls.append((self.extracted_ID, true_value, false_value))

class BinaryOpsVisitor(NodeVisitor):

    def __init__(self, module):
        self.module = module
        # preprocess begin ends and assigns
        mbev = MissignBeginEndVisitor(module)
        mbev.visit(module)
        # build datawidth table
        self.dwv = DatawidthVisitor()
        self.dwv.visit(module)

    def visit_Assign(self, node):
        print("ERROR: continuous assigns not supported, run preprocessor!")
        quit()

    def visit_Block(self, node):
        bv = BlockVisitor(node, self.module, self.dwv)
        # check if new decls to add:
        bv.generic_visit(node)
        #print(bv.new_decls)
        if bv.new_decls:
            for nd in bv.new_decls:
                # nd is (new_id, left, right)
                # for now go easy and just copy left one and see how it goes
                #print(self.dwv.signaltable)
                #print(nd)
                if isinstance(nd[1], IntConst):
                    w = self.dwv.signaltable[nd[1]]
                else:
                    w = self.dwv.signaltable[nd[1].name]
                new_decl = Decl([Wire(nd[0].name, width=w)])
                temp_list = list(self.module.items)
                temp_list.append(new_decl)
                self.module.items = tuple(temp_list)
                self.dwv.addEntry(nd[0].name, w)

class DatawidthVisitor(NodeVisitor):
    def __init__(self):
        self.signaltable={}

    def addEntry(self, name, width):
        if name not in self.signaltable or self.signaltable[name] == None:
            self.signaltable[name] = width

    def visit_Input(self, node):
        self.addEntry(node.name, node.width)

    def visit_Output(self, node):
        self.addEntry(node.name, node.width)

    def visit_Reg(self, node):
        self.addEntry(node.name, node.width)

    def visit_Wire(self, node):
        self.addEntry(node.name, node.width)
    
    def visit_IntConst(self,node):
        if "'" in node.value:
            width = Width(IntConst(int(node.value.split("'")[0])-1), IntConst(0))
        else:
            width = Width(IntConst(31), IntConst(0))
        self.addEntry(node, width)


class MissignBeginEndVisitor(NodeVisitor):        
    
    def __init__(self, module):
        self.module = module

    def visit_Always(self, node):
        if not isinstance(node.statement, Block):
            new_block = Block([node.statement])
            node.statement = new_block
        self.generic_visit(node)
    
    def visit_IfStatement(self, node):
        if not isinstance(node.true_statement, Block):
            new_block = Block([node.true_statement])
            node.true_statement = new_block
        if not isinstance(node.false_statement, Block):
            new_block = Block([node.false_statement])
            node.false_statement = new_block
        self.generic_visit(node)
    
    def visit_Case(self, node):
        if not isinstance(node.statement, Block):
            new_block = Block([node.statement])
            node.statement = new_block
        self.generic_visit(node)

    def visit_Assign(self, node):
        new_blockingSub = BlockingSubstitution(node.left,node.right)
        new_always = Always(SensList([Sens(None, 'all')]), Block([new_blockingSub]))
        temp_list = list(self.module.items)
        temp_list.remove(node)
        temp_list.append(new_always)
        self.module.items = tuple(temp_list)
    
