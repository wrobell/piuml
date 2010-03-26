import sys
import os.path

sys.path.append(os.path.abspath('src'))

import piuml

extensions = ['piuml.sphinx_ext', 'sphinx.ext.autodoc',
        'sphinx.ext.doctest', 'sphinx.ext.todo',]
    
project = 'piUML'
source_suffix = '.txt'
master_doc = 'index'

version = piuml.__version__
release = piuml.__version__
