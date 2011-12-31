piUML Language Reference
========================

Identifiers
-----------
The indentifiers

- must exist when references (i.e. by edges or alignment)
- cannot be duplicated

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


Relations
---------

Association
~~~~~~~~~~~

Comment Line
~~~~~~~~~~~~

Component Assembly
~~~~~~~~~~~~~~~~~~

Dependency
~~~~~~~~~~
- <<urime>>
- o) (o

Extension
~~~~~~~~~

Generalization
~~~~~~~~~~~~~~

Layout
------
Horizontal alignment operators
    top
    center
    bottom

Vertical alignment operators
    left
    middle
    right

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
There are two types of errors

    parser erros
        piUML language errors, which indicate problems in the source code.
    UML errors
        UML semantics errors.

Parsing Errors
~~~~~~~~~~~~~~
- string problem
- non-existing id

UML Errors
~~~~~~~~~~

