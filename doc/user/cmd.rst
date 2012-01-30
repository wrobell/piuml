Command Line Interface
======================

piUML software provides very simple command line user interface, which
allows to generate diagrams in different formats and process multiple input
files.

The help can be accessed with ``-h`` option::

    piuml -h

piUML generates PDF files by default. To create SVG or PNG files use ``-T``
option, for example::

    piuml -T svg model1.pml model2.pml

To process multiple model files simply list their names separated by space,
for example::

    piuml model1.pml model2.pml

.. vim: sw=4:et:ai
