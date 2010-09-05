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
Coordination System
===================
Cartesian coordinate system is assumed (x-axis leftward, y-axis upward),
which is aligned with standard geometry, MetaPost, PostScript, etc. but is
different with screen oriented systems.

Above needs to be considered carefully in case of vertical alignment, which
is done from top to bottom.
"""

from collections import namedtuple, MutableSequence
from uuid import uuid4 as uuid


# packaging elements
PELEMENTS = ('artifact', 'class', 'component', 'device', 'node',
        'instance', 'package', 'profile', 'subsystem')

# non-packaging elements
NELEMENTS = ('actor', 'comment', 'interface', 'metaclass', 'stereotype',
        'usecase')

# all UML elements
ELEMENTS = PELEMENTS + NELEMENTS

KEYWORDS = ('artifact', 'metaclass', 'component', 'device', 'interface',
        'profile', 'stereotype', 'subsystem')

Area = namedtuple('Area', 'top right bottom left')
_Pos = namedtuple('_Pos', 'x y')
Size = namedtuple('Size', 'width height')
# alignment constraints
AlignConstraints = namedtuple('AlignConstraints',
    'top right bottom left center middle span')


def ntype(cls):
    """
    Set type of parsed piUML language AST node, so it can be recognized by
    Spark parsing routines.
    """
    cls.type = cls.__name__.lower()
    return cls


class Pos(object):
    def __init__(self, x, y):
        self._pos = _Pos(x, y)


    def __getitem__(self, index):
        return self._pos[index]


    def _set_x(self, x):
        self._pos = Pos(x, self._pos.y)


    def _set_y(self, y):
        self._pos = Pos(self._pos.x, y)

    x = property(lambda s: s._pos.x, _set_x)
    y = property(lambda s: s._pos.y, _set_y)


class SpanMatrix(object):
    """
    Two dimensional matrix.

    The matrix is a list of lists organized in following manner::

              --       --
              | --- --- |
              | |A| |1| |
     m.data = |  B   2  |
              |  C   3  |
              | |D| |4| |
              | --- --- |
              --       --

    therefore, for example::

        m[0, 1] == B == m.data[0][1]
        m[1, 2] == 3 == m.data[1][2]

    """
    def __init__(self):
        self.data = []

    def __getitem__(self, (col, row)):
        return self.data[col][row]

    def __setitem__(self, (col, row), value):
        self.data[col][row] = value


    def insert_col(self, col):
        k = len(self.data[0]) if len(self.data) > 0 else 1
        self.data.insert(col, [None] * k)


    def insert_row(self, row):
        if self.data:
            for l in self.data:
                l.insert(row, None)
        else:
            self.data.append([None])


    def index(self, value):
        row = None
        for col, d in enumerate(self.data):
            try:
                row = d.index(value)
                break
            except ValueError:
                pass
                
        return None if row is None else (col, row)


    def dim(self):
        """
        Return matrix dimensions.
        """
        return (len(self.data), len(self.data[0])) if self.data else (0, 0)


    def hspan(self, a, b):
        pa = self.index(a)
        pb = self.index(b)
        if not pa and not pb:
            k, l = self.dim()
            self.insert_col(k)
            self[k, 0] = a
            self.insert_col(k + 1)
            self[k + 1, 0] = b
        elif pa and not pb:
            n, m = pa
            k, l = self.dim()
            if n + 1 == k or self[n + 1, m] != None:
                self.insert_col(n + 1)
            self[n + 1, m] = b
        elif not pa and pb:
            n, m = pb
            if n == 0:
                self.insert_col(0)
                self[0, m] = a
            elif self[n - 1, m] != None:
                self.insert_col(n - 1)
                self[n - 1, m] = a


    def vspan(self, a, b):
        pa = self.index(a)
        pb = self.index(b)
        if not pa and not pb:
            k, l = self.dim()
            self.insert_row(l)
            self[0, l] = a
            self.insert_row(l + 1)
            self[0, l + 1] = b
        elif pa and not pb:
            n, m = pa
            k, l = self.dim()
            if m + 1 == l or self[n, m + 1] != None:
                self.insert_row(m + 1)
            self[n, m + 1] = b
        elif not pa and pb:
            n, m = pb
            if m == 0:
                self.insert_row(0)
                self[n, 0] = a
            elif self[n, m - 1] != None:
                self.insert_row(m - 1)
                self[n, m - 1] = a


    def __str__(self):
        return str(self.data)



class Style(object):
    """
    Base style class for boxes and lines.
    """


class BoxStyle(Style):
    """
    Box style information.

    Rectangle of the box is defined by lower-left and upper-right corners.
    Thanks to this:
    
        BoxStyle.size = BoxStyle.ur - BoxStyle.ll

    :Attributes:
     ll
        Lower left corner.
     ur
        Upper right corner.
     head
        Head height.
    """
    def __init__(self):
        self.ll = Pos(0, 0)
        self.ur = Pos(0, 0)
        self.head = 0
        self.edges = (Pos(0, 0), Pos(0, 0))
        self.margin = Area(10, 10, 10, 10)
        self.padding = Area(5, 10, 5, 10)
        self.icon_size = Size(0, 0)
        self.min_size = Size(80, 40)
        self._set_size(self.min_size)


    def _get_size(self):
        return Size(self.ur.x - self.ll.x, self.ur.y - self.ll.y)

    def _set_size(self, size):
        w, h = size
        self.ur.x = self.ll.x + w
        self.ur.y = self.ll.y + h

    size = property(_get_size, _set_size)


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
        self.align = AlignConstraints([], [], [], [], [], [], SpanMatrix())

        # few exceptions to default style
        if cls == 'actor':
            self.style.padding = Area(0, 0, 0, 0)
            self.style.size = Size(40, 60)
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
     constraints
        All alignment constraints.
    """
    def __init__(self):
        super(Diagram, self).__init__('diagram')
        self.cache = {}
        self.order = []
        self.constraints = []

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


@ntype
class Dummy(Node):
    """
    Non-important part of piUML language like comment or whitespace.
    """


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


def lsb(parent, kids):
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


# vim: sw=4:et:ai
