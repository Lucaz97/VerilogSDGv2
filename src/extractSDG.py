import os  
from optparse import OptionParser
import pyverilog.vparser.ast as vast
from pyverilog.vparser.parser import VerilogCodeParser
from SystemDependenceGraph.SystemDependencyGraph import *
from Preprocessing.signalvisitor import BinaryOpsVisitor
from Preprocessing.signalvisitor import MissignBeginEndVisitor 
from Preprocessing.modulevisitor import ModuleVisitor as mvisit
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

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

    def __init__(self, options):
        self.target = options.target
        self.top = options.top
        self.verbose = options.verbose
        self.filelist = []
        self.includes = []
        self.defines = []
        if options.file_list:
            if not os.path.exists(options.file_list): raise IOError("Verilog command file not found: " + options.file_list)
            self.parse_verilog_options(options.file_list)
        for i in options.include:
            self.includes.append(i)
        for d in options.define:
            self.defines.append(d)
        for f in self.filelist:
            if not os.path.exists(f): raise IOError("file not found: " + f)


def main():
    
    optparser = OptionParser()

    optparser.add_option("-o","--target-dir",dest="target",action="store",
                         default="work",help="Include path")
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

    (options, args) = optparser.parse_args()
    if not options.top:
        optparser.error('Top module name not given')
    if not options.file_list:
        optparser.error('File list not given')

    cfg = Config(options)

    codeparser = VerilogCodeParser(cfg.filelist, preprocess_include=cfg.includes, preprocess_define=cfg.defines, debug=False)
    ast = codeparser.parse()
    if cfg.verbose:
        ast.show()
    

    mv = mvisit()
    mv.visit(ast)
    modulenames = mv.get_modulenames()
    for module in modulenames:
        mod_node = mv.get_moduleinfotable().getDefinition(module)
        bov = BinaryOpsVisitor(mod_node)
        bov.visit(mod_node)
    outfile = open("out.v", 'w')
    codegen = ASTCodeGenerator()
    ast.show()
   
    print(codegen.visit(ast), file=outfile)

    sdg = SystemDependencyGraph(ast, cfg.top)

    if options.all:
        sdg.draw_modules()
    
    sdg.draw("sdg")

if __name__ == '__main__':
    main()