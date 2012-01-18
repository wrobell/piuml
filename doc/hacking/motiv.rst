Motivation
==========

Most of the modeling tools supporting UML are GUI and WYSIWYG based. It is
commonly believed that such approach lowers barrier for a lot of computing
tasks, including diagramming and modeling.

There is also another view, which sees GUI and WYSIWYG tools as quite limiting.
For example, in the context of UML modeling

- changes and searching across multiple models can be time consuming, i.e.
  comparing to Unix tools like grep, awk or sed
- version management of a model is hard, i.e. viewing differences, merging two
  versions
- automated integration with publishing or documentation systems like TeX or
  reStructuredText is almost non-existent as usually manual exporting of
  diagrams is required
- embedding diagrams in textual communication (e-mail, instant messaging)
  requires HTML support at least

Above limitations could be avoided with textual, declarative modeling system
with well defined language and support for visualization of models in UML
notation. Advantages of such system could be as follows

- can be created and modified with any text editor
- multiple changes of models, refactoring and searching is supported with
  common, well established text tools 
- any SCM can be used for easy and convenient model version management
- embedding of simple diagrams in textual communication is instant

`UMLGraph <http://www.umlgraph.org/>`_ [GUML2003]_ project provides above
qualities, but its language is Java based and `Graphviz
<http://www.graphviz.org/>`_ is used as layout system, which have the following
disadvantages

- the Java notation is quite verbose and does not reflect UML notation, i.e.
  visibility of class methods and attributes
- the Graphviz is crafted towards automated graph layout with little support for
  layout control and subgraphs, which cause problems when order of UML elements
  is important and limits support for UML element packaging (i.e. components
  within components)

Therefore, the piUML project was born with the following concepts in mind

- piUML is declarative, textual language for modeling with succint syntax
  inspired by Python and reStructuredText
- the language supports UML terminology and notation, i.e. appropriate language
  elements naming, attributes and methods visibility, stereotypes, constraints
  in Object Constraint Language (OCL), etc.
- modeling and visualization of structures containing other structures (UML
  elements packaging) is supported on the language level
- generated diagrams are UML compliant
- UML diagram generation utilizes automatic elements layout and line routing
  algorithms with ability to control their parameters, i.e. alignment, order of
  elements on a diagram, etc.
- separation of content and presentation

Ability to describe models in declarative way can enable others to experiment
with voice based interfaces or automated, spatial and flexible GUI (i.e. gesture
based). While such research is beyond scope of this project, then appropriate
API could be maintained to support various user interface ideas.

References
----------
.. [GUML2003] Diomidis Spinellis, `"On the Declarative Specification of Models" <http://www.spinellis.gr/pubs/jrnl/2003-IEEESW-umlgraph/html/article.html>`_, http://www.spinellis.gr/pubs/jrnl/2003-IEEESW-umlgraph/html/article.html

.. vim: sw=4:et:ai
