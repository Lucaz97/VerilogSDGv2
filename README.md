
# Verilog-SDG-Extraction
Verilog System Dependence Graph Extraction

### Dependencies:
pygraphviz

	$ sudo apt-get install graphviz graphviz-dev
	$ pip install pygraphviz
If you have any problems please check https://pygraphviz.github.io/documentation/stable/install.html

### Options:

    -o --target-dir
 Target directory, default: work
 

    -t --top
  Top module
  

    -f --file-list
  Design file list
   

    -a --all
  Extract SDGs of all modules, if not set, only SDG of top module is generated.
 

    -v
   Verbose
Makefiles in tests designs are ready to be launched

To open the files you can use xDOT:
	$ sudo apt install xdot
