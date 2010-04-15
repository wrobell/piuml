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


# packaging element
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
    'top right bottom left center middle hspan vspan')


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


# todo: rename to BoxNode and create LineNode
class Node(list):
    """
    Parsed piUML language data.

    Contains preprocessed UML element data like name and applied
    stereotypes.

    The class itself is a list and may contain additional nodes as its
    children. The children maybe
    
    - attributes and operation of a class
    - artifacts deployed within a node
    - actions in a partition (swimlane)

    :Attributes:
     type
        Basic node type.
     id
        Node identifier. It should be unique.
     parent
        Parent node.
     element
        UML element type, i.e. class, association, etc.
     name
        Name of named element (i.e. class). Empty by default and empty for
        non-named elements (i.e. dependency).
     stereotypes
        List of stereotypes applied to an element.
     style
        Style information of rendered node.
     data
        Additional node data, i.e. in case of association its ends
        navigability information.
    """
    def __init__(self, type, element, name='', data=None, id=None):
        super(Node, self).__init__()
        self.parent = None
        self.type = type
        self.element = element
        if id is None:
            self.id = str(uuid())
        else:
            self.id = id
        self.name = name
        self.stereotypes = []
        self.data = data if data else {}
        self.style = BoxStyle()
        self.align = AlignConstraints([], [], [], [], [], [], [], [])

        # few exceptions to default style
        if element == 'actor':
            self.style.padding = Area(0, 0, 0, 0)
            self.style.size = Size(40, 60)
        elif element == 'association':
            self.style.padding = Area(3, 18, 3, 18)
        elif element in ('artifact', 'component'):
            self.style.icon_size = Size(10, 15)
        elif element == 'fdiface':
            self.style.min_size = Size(30, 30)
            self.style.size = Size(30, 30)


    def is_packaging(self):
        """
        Check is UML element is packaging other UML elements.
        """
        return len([n for n in self if n.element in ELEMENTS]) > 0


    def unwind(self):
        yield self
        for i in self:
            for j in i.unwind():
                yield j


    def __str__(self):
        return self.element + ': ' + '[%s]' % ','.join(str(k) for k in self)


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


class NodeList(Node):
    """
    List of nodes.

    :Attributes:
     data
        List of nodes.
    """
    def __init__(self, type, element):
        super(NodeList, self).__init__(type, element)
        self.data = []


class AST(Node):
    """
    Root node of abstract syntax tree.

    :Attributes:
     cache
        Cache of nodes by their id.
     order
        Order of nodes (LR then TB).
     constraints
        All alignment constraints.
    """
    def __init__(self):
        super(AST, self).__init__('diagram', 'diagram')
        self.cache = {}
        self.order = []
        self.constraints = []

    def reorder(self):
        self.order = [k for k in self.unwind()]


class Align(NodeList):
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
     align
        Alignment type.
    """
    def __init__(self, align):
        super(Align, self).__init__('align', align)


class Edge(Node):
    """
    Edge between nodes like association, dependency, comment line, etc.

    :Attributes:
     tail
        Tail node.
     head
        Head node. 
    """
    def __init__(self, type, element, tail, head, name='', data=[]):
        super(Edge, self).__init__(type, element, name, data)
        self.tail = tail
        self.head = head
        self.style.padding = Area(3, 10, 3, 10)


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
