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

from collections import namedtuple
from uuid import uuid4 as uuid

# UML elements
ELEMENTS = ('actor', 'artifact', 'comment', 'class', 'component', 'device',
    'interface', 'instance', 'metaclass', 'node', 'package', 'profile',
    'stereotype', 'subsystem', 'usecase')

Area = namedtuple('Area', 'top right bottom left')
Pos = namedtuple('Pos', 'x y')
Size = namedtuple('Size', 'width height')

class Style(object):
    """
    Node style information.
    """
    def __init__(self):
        self.pos = Pos(0, 0)
        self.size = Size(0, 0)
        self.edges = ()
        self.margin = Area(0, 0, 0, 0)
        self.padding = Area(5, 10, 5, 10)
        self.inner = Area(0, 0, 0, 0)


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
    def __init__(self, type, element, name='', data=None):
        super(Node, self).__init__()
        self.parent = None
        self.type = type
        self.element = element
        self.id = str(uuid())
        self.name = name
        self.stereotypes = []
        self.data = data if data else {}
        self.style = Style()


    def is_packaging(self):
        """
        Check is UML element is packaging other UML elements.
        """
        return len([n for n in self if n.element in ELEMENTS]) > 0



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


# vim: sw=4:et:ai
