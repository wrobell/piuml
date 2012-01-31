piUML Language Reference
========================

Identifiers
-----------
The indentifiers

- are unique, i.e. two elements like class and interface cannot have the
  same id
- must exist when referenced, i.e. by relationships or alignment

UML Elements
------------

Elements:

==========  ===========  ===============  ===================
 Keyword     Packaging     Compartments       Description
==========  ===========  ===============  ===================
actor           No          No            Actor icon (human shape)
artifact        Yes         Yes       
comment         No          No        
class           Yes         Yes       
component       Yes         Yes       
device          Yes         Yes       
interface       No          Yes       
instance        Yes         Yes       
metaclass       No          Yes       
node            Yes         Yes       
package         Yes         Yes       
profile         Yes         Yes       
stereotype      No          Yes       
subsystem       Yes         Yes       
usecase         No          No        
==========  ===========  ===============  ===================


UML Relationships
-----------------

Association
~~~~~~~~~~~

Comment Line
~~~~~~~~~~~~

Component Assembly
~~~~~~~~~~~~~~~~~~

Dependency
~~~~~~~~~~
.. - <<urime>>
.. - o) (o

Extension
~~~~~~~~~

Generalization
~~~~~~~~~~~~~~

Layout
------
Horizontal alignment operators

- top
- center
- bottom

Vertical alignment operators

- left
- middle
- right

Default layout alignment is middle.

Examples::

    a b c
    center: b c

    a b
      c


    a b c d
    center: c d

    a b c
        d


    a b c d e
    center: a b
    center: d e

    a c d
    b   e


The operators change current layout alignment. It is possible to change 
it few times, for example::

    a b c
    center: b c
    top: c b    # overrides usage of 'center' operator above

    a c b

The purpose of above is to allow to override default alignment, i.e. when
a diagram is imported by new diagram.

Errors
------
There are three types of errors

    parser erros
        piUML language errors, which indicate problems in the source code.
    UML errors
        UML semantics errors, when a construction is invalid due to UML
        constraints.
    alignment errors
        Alignment errors are raised when diagram alignment is invalid or
        impossible to obtain.

..  Parsing Errors
..  ~~~~~~~~~~~~~~
..  - string problem
..  - non-existing id

.. UML Errors
.. ~~~~~~~~~~

.. vim: sw=4:et:ai
