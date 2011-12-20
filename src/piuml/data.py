#
# piUML - UML diagram generator.
#
# Copyright (C) 2010 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Coordinate System
=================
Screen oriented coordinate system is assumed (x-axis leftward, y-axis
downard), which is aligned with Cairo.
"""

from collections import namedtuple, MutableSequence, Iterable
from uuid import uuid4 as uuid
import logging

log = logging.getLogger('piuml.data')


# packaging elements
PELEMENTS = ('artifact', 'class', 'component', 'device', 'node',
        'instance', 'package', 'profile', 'subsystem')

# non-packaging elements
NELEMENTS = ('actor', 'comment', 'interface', 'metaclass', 'stereotype',
        'usecase')

# all supported UML elements
ELEMENTS = PELEMENTS + NELEMENTS

KEYWORDS = ('artifact', 'metaclass', 'component', 'device', 'interface',
        'profile', 'stereotype', 'subsystem')



class Pos(object):
    __slots__ = 'x', 'y'

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

    def __str__(self):
        return '(%s, %s)' % (self.x, self.y)

    def __eq__(self, p):
        return self.x == p.x and self.y == p.y

    def __repr__(self):
        return 'Pos({},{})'.format(self.x, self.y)


class Size(object):
    __slots__ = 'width', 'height'

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __iter__(self):
        return iter((self.width, self.height))

    def __str__(self):
        return '%s, %s' % (self.width, self.height)


class Area(object):
    __slots__ = 'top', 'right', 'bottom', 'left'

    def __init__(self, top, right, bottom, left):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def __iter__(self):
        return iter((self.top, self.right, self.bottom, self.left))


def ntype(cls):
    """
    Set type of parsed piUML language AST node, so it can be recognized by
    Spark parsing routines.
    """
    cls.type = cls.__name__.lower()
    return cls



class Style(object):
    """
    Base style class for boxes and lines.
    """
    def __init__(self):
        self.margin = Area(10, 10, 10, 10)
        self.padding = Area(5, 10, 5, 10)



class BoxStyle(Style):
    """
    Box style information.

    Rectangle of the box is defined by its position and size.

    Box has compartments. There is at least one compartment containing
    information like UML stereotypes, name of UML named element or simply
    other boxes.

    Box may have an icon, which is displayed in top right corner of the
    box, i.e. UML artifact or UML component icon.

    :Attributes:
     pos
        Box position.
     size
        Current size of the box.
     min_size
        Minimum size of the box.
     compartment
        Height of each compartment.
     icon_size
        Icon size.
    """
    def __init__(self):
        """
        Create box style information.
        """
        super(BoxStyle, self).__init__()

        # box specific
        self.pos = Pos(0, 0)
        self.size = Size(80, 40)
        self.icon_size = Size(0, 0)
        self.min_size = Size(80, 40)
        self.compartment = [0]



class LineStyle(Style):
    """
    Line style.

    :Attributes:
     edges
        List of line points. 
    """
    def __init__(self):
        """
        Create line style information.
        """
        super(LineStyle, self).__init__()
        self.min_length = 100
        self.edges = (Pos(0, 0), Pos(0, 0))



class Node(list):
    """
    Parsed piUML language node.

    Contains preprocessed UML data like name and applied
    stereotypes.

    The class itself is a list and may contain additional nodes as its
    children. The children may be
    
    - attributes and operation of a class
    - artifacts deployed within a node
    - actions in a partition (swimlane)

    :Attributes:
     type
        Basic node type.
     cls     
        Particularizes node type, which can be an UML class (element,
        relationship) or subtype of other part of piUML language (i.e.
        section type, align type, etc.).
     id
        Node identifier. It should be unique.
     parent
        Parent node.
     name
        Name of named element (i.e. class). Empty by default and empty for
        non-named elements (i.e. dependency).
     stereotypes
        List of stereotypes applied to an UML class.
     style
        Style information of rendered node.
     data
        Additional node data, i.e. in case of association its ends
        navigability information.
    """
    type = None

    def __init__(self, cls, name='', data=None, id=None):
        super(Node, self).__init__()
        self.parent = None
        self.cls = cls
        if id is None:
            self.id = str(uuid())
        else:
            self.id = id
        self.name = name
        self.stereotypes = []
        self.data = data if data else {}
        self.style = BoxStyle()

        # few exceptions to default style
        if cls == 'actor':
            self.style.padding = Area(0, 0, 0, 0)
            self.style.size = Size(40, 60)
        elif cls in ('package', 'profile'):
            self.style.size = Size(80, 60)
        elif cls == 'association':
            self.style.padding = Area(3, 18, 3, 18)
        elif cls in ('artifact', 'component'):
            self.style.icon_size = Size(10, 15)
        elif cls == 'fdiface':
            self.style.min_size = Size(30, 30)
            self.style.size = Size(30, 30)
        elif cls == 'node':
            self.style.margin = Area(20, 20, 10, 10)


    def is_packaging(self):
        """
        Check is UML element is packaging other UML elements.
        """
        return len([n for n in self if n.cls in ELEMENTS]) > 0


    def unwind(self):
        yield self
        for i in self:
            for j in i.unwind():
                yield j


    def __str__(self):
        return self.cls + ': ' + '[%s]' % ','.join(str(k) for k in self)


    def __repr__(self):
        return self.id


    def __hash__(self):
        """
        AST nodes are hashed with their id's hash value.
        """
        return self.id.__hash__()


    def __eq__(self, other):
        """
        Equality comparision of AST nodes is their id equality.
        """
        return isinstance(other, Node) and self.id == other.id


@ntype
class Diagram(Node):
    """
    Diagram node.
    
    Diagram node is root node of parsed abstract syntax tree (AST) of
    diagram written in piUML language.

    :Attributes:
     cache
        Cache of nodes by their id.
     order
        Order of nodes (LR then TB).
    """
    def __init__(self):
        super(Diagram, self).__init__('diagram')
        self.cache = {}
        self.order = []

    def reorder(self):
        self.order = [k for k in self.unwind()]


@ntype
class Element(Node):
    """
    Representation of UML element like class, component, node, etc.
    """


@ntype
class Feature(Node):
    """
    Representation of UML feature like attribute or operation.
    """


@ntype
class IElement(Node):
    """
    Representation of UML element having form of an icon, i.e. assembly
    connector, iconified interface, activity nodes.
    """


@ntype
class Line(Node):
    """
    Representation of UML relationship like association, dependency,
    comment line, etc.

    :Attributes:
     tail
        Tail node.
     head
        Head node. 
    """
    def __init__(self, cls, tail, head, name='', data=[]):
        super(Line, self).__init__(cls, name, data)
        self.style = LineStyle()
        self.tail = tail
        self.head = head
        self.style.padding = Area(3, 10, 3, 10)


@ntype
class Section(Node):
    """
    Section in a diagram written in piUML language.

    There is only one section currently specified - 'layout'.
    """


@ntype
class Align(Node):
    """
    Alignment definition information.

    Alignment type may be one of:
    - left
    - right
    - top
    - bottom
    - center
    - middle

    :Attributes:
     cls
        Alignment type.
    """
    def __init__(self, cls):
        super(Align, self).__init__(cls)
        self.nodes = []


class Stereotype(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return 'Stereotype({})'.format(self.name)


class Element(object):
    def __init__(self, cls=None, id=None, stereotypes=None, name=None, data=None):
        self.cls = cls
        self.id = id
        self.name = name
        self.stereotypes = stereotypes
        self.parent = None
        self.data = {} if data is None else data


    def __repr__(self):
        return '{} {} {} {}'.format(self.cls, self.id, self.name,
                self.stereotypes)



class PackagingElement(Element):
    def __init__(self, *args, **kw):
        super(PackagingElement, self).__init__(*args, **kw)
        self.children = []


    def __getitem__(self, k):
        return self.children[k]


    def __iter__(self):
        return iter(self.children)


    def __repr__(self):
        return super(PackagingElement, self).__repr__() \
                + ' {}'.format(self.children)



class Diagram(PackagingElement):
    """
    UML diagram instance.

    :Attributes:
     children
        Diagram elements.
    """
    def __init__(self, children):
        """
        Create UML diagram instance.
        """
        super(Diagram, self).__init__(cls='diagram', id='diagram')

        self.children = list(children)

        log.debug('diagram children {}'.format(self.children))
        for k in self.children:
            k.parent = self


class Relationship(Element):
    """
    Representation of UML relationship like association, dependency,
    comment line, etc.

    :Attributes:
     tail
        Tail node.
     head
        Head node. 
    """
    def __init__(self, cls, tail, head, stereotypes=None, name='',
            data=None):
        super(Relationship, self).__init__(cls=cls,
                stereotypes=stereotypes, name=name)
        self.data = {} if data is None else data
        self.style = LineStyle()
        self.tail = tail
        self.head = head
        self.style.padding = Area(3, 10, 3, 10)



class Mult(object):
    """
    Attribute multiplicity.
    """
    def __init__(self, lower=None, upper=None):
        """
        Create multiplicity instance.
        """
        self.lower = lower
        self.upper = upper

        if lower is None:
            self.lower = '0'
        if upper is None:
            self.upper = '*'


    def __str__(self):
        """
        Convert multiplicity into string.
        """
        if self.lower == self.upper:
            return '[{}]'.format(self.lower)
        else:
            return '[{}..{}]'.format(self.lower, self.upper)



class Feature(object):
    """
    UML feature (attribute, operation) representation.
    """



class Attribute(Feature):
    """
    UML attribute representation.
    """
    def __init__(self, name, type, mult):
        super(Attribute, self).__init__()
        self.name = name
        self.type = type
        self.mult = mult


    def __repr__(self):
        """
        Return UML attribute string representation.
        """
        return '{} {} {}'.format(self.name, self.type, self.mult)


class Operation(Feature):
    """
    UML operation representation.
    """
    def __init__(self, name):
        super(Operation, self).__init__()
        self.name = name


def lca(ast, *args):
    """
    Find lowest common ancestor for specified nodes.
    """
    parents = []
    for n in args:
        p = set()
        k = n
        while k.parent:
            p.add(k.parent)
            k = k.parent
        parents.append(p)
    p = parents.pop()
    while len(parents) > 0:
        p.intersection_update(parents.pop())

    data = sorted(p, key=ast.order.index)
    return data[-1]


def lsb(parent, *kids):
    """
    Given parent node and its (direct or non-direct) descendants find
    nodes, which are direct descendants of parent (or are siblings).
    """
    siblings = []
    for k in kids:
        # k at least 2 levels lower
        if k.parent != parent:
            pp = k.parent
            while pp.parent != parent:
                pp = pp.parent
            siblings.append(pp)
        else:
            siblings.append(k)
    return siblings


def unwind(n):
    yield n

    if not isinstance(n, Iterable):
        return
    for k1 in n:
        if isinstance(k1, Iterable):
            for k2 in unwind(k1):
                yield k2

# vim: sw=4:et:ai
