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

from collections import Iterable
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



class Stereotype(object):
    """
    Stereotype information.

    :Attributes:
     name
        Name of stereotype.
    """
    is_keyword = property(lambda s: s.name in KEYWORDS)

    def __init__(self, name):
        self.name = name


    def __repr__(self):
        return 'Stereotype({})'.format(self.name)



class Element(object):
    """
    Basic representation of UML element like interface, action, etc.

    Contains preprocessed UML data like name and applied
    stereotypes.

    :Attributes:
     cls     
        Particularizes node type, which can be an UML class (element,
        relationship).
     id
        Element unique identifier.
     parent
        Parent node.
     stereotypes
        List of stereotypes applied to an UML class.
     name
        Name of named element (i.e. class). Empty by default and empty for
        non-named elements (i.e. dependency).
     data
        Additional node data, i.e. in case of association its ends
        navigability information.
    """
    def __init__(self, cls=None, id=None, stereotypes=None, name=None, data=None):
        self.cls = cls
        self.id = str(uuid()) if id is None else id
        self.name = '' if name is None else name
        self.stereotypes = stereotypes
        self.parent = None
        _data = {
            'attributes': [],
            'operations': [],
            'stattrs': [], 
        }
        self.data = _data if data is None else data


    def __repr__(self):
        return '{} {} {} {}'.format(self.cls, self.id, self.name,
                self.stereotypes)


    def __hash__(self):
        """
        AST nodes are hashed with their id's hash value.
        """
        return self.id.__hash__()


    def __eq__(self, other):
        """
        Equality comparision of AST nodes is their id equality.
        """
        return isinstance(other, Element) and self.id == other.id



class PackagingElement(Element):
    """
    Packaging UML element like package, component, etc.

    :Attributes:
     children
        Elements packaged by the element.
    """
    def __init__(self, *args, children=None, **kw):
        super(PackagingElement, self).__init__(*args, **kw)
        self.children = [] if children is None else list(children)


    def __getitem__(self, k):
        """
        Get packaged element.

        :Parameters:
         k
            Index of packaged element.
        """
        return self.children[k]


    def __iter__(self):
        """
        Iterate over packaged elements.
        """
        return iter(self.children)


    def __len__(self):
        """
        Return amount of packaged elements.
        """
        return len(self.children)


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
    def __init__(self, children=[]):
        """
        Create UML diagram instance.
        """
        super(Diagram, self).__init__(cls='diagram', id='diagram',
                children=children)

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
                stereotypes=stereotypes,
                name=name,
                data=data)
        self.tail = tail
        self.head = head



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
            self.upper = self.lower


    def __str__(self):
        """
        Convert multiplicity into string.
        """
        assert self.lower is not None
        assert self.upper is not None
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
    def __init__(self, name, type, value, mult):
        super(Attribute, self).__init__()
        self.name = '' if name is None else name
        self.type = type
        self.value = value
        self.mult = mult


    def __repr__(self):
        """
        Return UML attribute string representation.
        """
        t = self.name
        if self.type is not None:
            t += ': {}'.format(self.type)
        if self.value is not None:
            t += ' = {}'.format(self.value)
        if self.mult is not None:
            t += ' {}'.format(self.mult)
        return t


class Operation(Feature):
    """
    UML operation representation.
    """
    def __init__(self, name):
        super(Operation, self).__init__()
        self.name = name



class Section(object):
    """
    Section in a diagram written in piUML language.

    There is only one section currently specified - 'layout'.
    """
    def __init__(self, name):
        self.name = name
        self.data = []


class Align(object):
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
     type
        Alignment type.
    """
    def __init__(self, type):
        self.type = type
        self.nodes = []


def preorder(n, f, reverse=False):
    """
    Traverse a tree in preorder.

    :Parameters:
     n
        Tree root.
     f
        Function to visit a node when traversing.
     reversed
        Visit siblings in reversed order.
    """
    f(n)
    if isinstance(n, Iterable):
        n = reversed(n) if reverse else n
        for k in n:
            preorder(k, f)


def postorder(n, f):
    """
    Traverse a tree in postorder.

    :Parameters:
     n
        Tree root.
     f
        Function to execute on a node when traversing.
    """
    if isinstance(n, Iterable):
        for k in n:
            postorder(k, f)
    f(n)


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

    data = list(p) # fixme: sorted(p, key=ast.order.index)
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


class MWalker(object):
    """
    Walk a tree and execute a method on each traversed node.
    """
    def preorder(self, n, reverse=False):
        preorder(n, self, reverse)


    def postorder(self, n):
        postorder(n, self)


    def __call__(self, n):
        fn = 'v_{}'.format(n.__class__.__name__.lower())
        if hasattr(self, fn):
            f = getattr(self, fn)
            f(n)
        else:
            log.debug('no visitor method {}'.format(fn))


def unwind(n):
    yield n

    if not isinstance(n, Iterable):
        return
    for k1 in n:
        if isinstance(k1, Iterable):
            for k2 in unwind(k1):
                yield k2
        else:
            yield k1

# vim: sw=4:et:ai
