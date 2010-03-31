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

from collections import namedtuple, MutableSequence
from uuid import uuid4 as uuid
from gaphas import solver

# UML elements
ELEMENTS = ('actor', 'artifact', 'comment', 'class', 'component', 'device',
    'interface', 'instance', 'metaclass', 'node', 'package', 'profile',
    'stereotype', 'subsystem', 'usecase')

KEYWORDS = ('artifact', 'metaclass', 'component', 'device', 'interface',
        'profile', 'stereotype', 'subsystem')

Area = namedtuple('Area', 'top right bottom left')
#Pos = namedtuple('Pos', 'x y')
Size = namedtuple('Size', 'width height')
# alignment constraints
AlignConstraints = namedtuple('AlignConstraints',
    'top right bottom left center middle hspan vspan')

class Pos(object):
    _x = solver.solvable(varname='_v_x')
    _y = solver.solvable(varname='_v_y')

    def __init__(self, x, y, strength=solver.NORMAL):
        self._x, self._y = x, y
        self._x.strength = strength
        self._y.strength = strength


    def __getitem__(self, index):
        return (self.x, self.y)[index]


    def _set_x(self, x):
        self._x = x


    def _set_y(self, y):
        self._y = y


    def __str__(self):
        return '<%s at (%g, %g)>' % (self.__class__.__name__, float(self._x), float(self._y))

    x = property(lambda s: s._x, _set_x)
    y = property(lambda s: s._y, _set_y)

    __repr__ = __str__

class Style(object):
    """
    Node style information.
    """
    def __init__(self):
        self.pos = Pos(0, 0)
        self.p2 = Pos(0, 0)
        self.edges = (Pos(0, 0), Pos(0, 0))
        self.margin = Area(10, 10, 10, 10)
        self.padding = Area(5, 10, 5, 10)
        self.inner = Area(0, 0, 0, 0)
        self.icon_size = Size(0, 0)


    def _get_size(self):
        return Size(self.p2.x - self.pos.x, self.p2.y - self.pos.y)

    def _set_size(self, size):
        w, h = size
        self.p2.x = self.pos.x + w
        self.p2.y = self.pos.y + h

    size = property(_get_size, _set_size)


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
        self.style = Style()
        self.align = AlignConstraints([], [], [], [], [], [], [], [])

        # few exceptions for default style
        if element == 'actor':
            self.style.padding = Area(0, 0, 0, 0)
        elif element == 'association':
            self.style.padding = Area(3, 18, 3, 18)
        elif element in ('artifact', 'component'):
            self.style.icon_size = Size(10, 15)


    def is_packaging(self):
        """
        Check is UML element is packaging other UML elements.
        """
        return len([n for n in self if n.element in ELEMENTS]) > 0


    def __str__(self):
        return self.element + ': ' + '[%s]' % ','.join(str(k) for k in self)


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


def unwind(node):
    yield node
    for i in node:
        for j in unwind(i):
            yield j


def lca(ast, *args):
    """
    Find lowest common ancestor for specified nodes.
    """
    parents = []
    for n in args:
        p = set()
        k = n
        while k.parent:
            p.add(k.parent.id)
            k = k.parent
        parents.append(p)
    p = parents.pop()
    while len(parents) > 0:
        p.intersection_update(parents.pop())

    node_cache = dict(((k.id, k) for k in unwind(ast)))
    node_index = [k.id for k in unwind(ast)]
    data = sorted(p, key=node_index.index)
    return node_cache[data[-1]]


# vim: sw=4:et:ai
