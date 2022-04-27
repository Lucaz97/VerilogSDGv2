from curses import keyname
import os  
from optparse import OptionParser

from pyverilog.vparser.parser import VerilogCodeParser
from SystemDependenceGraph.SystemDependencyGraph import *
from Preprocessing.signalvisitor import BinaryOpsVisitor
from Preprocessing.modulevisitor import ModuleVisitor as mvisit
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import os

class Config:
    def parse_verilog_options(self, file_list):
        file = open(file_list, "r")
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.find("+incdir+") != -1:
                inc_string = line.split("+incdir+",1)[1]
                includes = inc_string.split("+")
                for i in includes:
                    self.includes.append(i)
            elif line.find("+define+") != -1:
                def_string = line.split("+define+", 1)[1]
                defines = def_string.split("+")
                for d in defines:
                    self.defines.append(d)
            else:
                self.filelist.append(line)

    def __init__(self, options, args):
        self.target = options.target
        self.top = options.top
        self.verbose = options.verbose
        self.filelist = []
        self.includes = []
        self.defines = []
        self.key_name = options.key_name
        if options.file_list:
            if not os.path.exists(options.file_list): raise IOError("Verilog command file not found: " + options.file_list)
            self.parse_verilog_options(options.file_list)
        
        for a in args:
            self.filelist.append(a)
        for i in options.include:
            self.includes.append(i)
        for d in options.define:
            self.defines.append(d)
        for f in self.filelist:
            if not os.path.exists(f): raise IOError("file not found: " + f)


def gen_formality(path, top):
    base_path = path + "formality/"
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    f = open(base_path+"eq_check.tcl", "w")
    print("read_verilog -container r -libname WORK -05 { ../original_design.v }",file=f)
    print("set_top r:/WORK/"+top,file=f)
    print("read_verilog -container i -libname WORK -05 { ../processed_design.v }",file=f)
    print("set_top i:/WORK/"+top,file=f)
    print("match",file=f)
    print("verify",file=f)


def main():
    
    optparser = OptionParser()

    optparser.add_option("-o","--target-dir",dest="target",action="store",
                         default="work/",help="Include path")
    optparser.add_option("-t","--top",dest="top",action="store",
                         help="Top module name")
    optparser.add_option("-f", "--file-list", dest="file_list", action="store",
                        default=False, help="Specify file with command-line options for the Verilog compiler")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    optparser.add_option("-a", "--all", dest="all", action="store_true",
                         default=False, help="Output SDG of all modules instad of top module only")
    optparser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                         default=False, help="Verbose execution") 
    optparser.add_option("-i", "--index", action="store", dest="index",
                         default=0, help="starting index for counting nodes", type="int")  
    optparser.add_option("-F", "--formality", action="store_true", dest="formality",
                         default=False, help="run formality to check equivalence between original design and processed design")  
    optparser.add_option("-k", "--key_name", action="store", dest="key_name",
                         default="locking_key", help="run formality to check equivalence between original design and processed design")  
    optparser.add_option("-r", "--relocking", action="store_true", dest="relocking",
                         default=False, help="is relocking")  
    optparser.add_option("-y", "--keyfile", action="store", dest="keyfile",
                         default=False, help="keyfile") 
    (options, args) = optparser.parse_args()
    if not options.top:
        optparser.error('Top module name not given')
    

    cfg = Config(options, args)

    if not cfg.filelist:
        optparser.error('No modules were given')

    codeparser = VerilogCodeParser(cfg.filelist, preprocess_include=cfg.includes, preprocess_define=cfg.defines, debug=False)
    ast = codeparser.parse()

    if cfg.verbose:
        ast.show()
    if not os.path.exists(options.target):
        os.makedirs(options.target)

    outfile = open(options.target+"original_design.v", 'w')
    codegen = ASTCodeGenerator()
    print(codegen.visit(ast), file=outfile)
    b = open("ast_orig.txt", "w")
    ast.show(buf=b)
    mv = mvisit()
    mv.visit(ast)
    modulenames = mv.get_modulenames()
    for module in modulenames:
        mod_node = mv.get_moduleinfotable().getDefinition(module)
        bov = BinaryOpsVisitor(mod_node)
        bov.visit(mod_node)
    outfile = open(options.target+"processed_design.v", 'w')
    codegen = ASTCodeGenerator()
    b = open("ast.txt", "w")
    ast.show(buf=b)
   
    print(codegen.visit(ast), file=outfile)

    sdg = SystemDependencyGraph(ast, cfg.top)

    keyfile = open(options.keyfile, "r")
    keyfile.readline()
    key=list(reversed(keyfile.readline()))
    print(key)
    
    #sdg.draw("sdg")

    sdg.print_graph(options.target+"sdg", options.index, options.key_name, options.relocking, key)

    if options.formality:
        gen_formality(options.target, options.top)
    
    print("!DONE!")

if __name__ == '__main__':
    main()

