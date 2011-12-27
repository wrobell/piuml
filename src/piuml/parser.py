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
piUML language parser.
"""

import lepl as P

import re
import logging

from piuml.data import Diagram, Element, PackagingElement, \
        IElement, Relationship, Mult, Attribute, Operation, \
        Section, Align, NELEMENTS, PELEMENTS, KEYWORDS

log = logging.getLogger('piuml.parser')

class ParseError(Exception):
    """
    piUML language parsing exception.
    """
    def __init__(self, msg):
        super(ParseError, self).__init__(msg)
        self.msg = msg



class UMLError(ParseError):
    """
    UML semantics error. Raised when some UML semantics error is
    discovered.
    """



class AlignmentError(ParseError):
    """
    Alignment error. Raised when some specified alignment is invalid
    or impossible to obtain.
    """



class NodeCache(dict):
    """
    Cache of nodes.

    A node is accessed by its id.

    Duplicate id's are disallowed - an error is raised when trying to
    replace existing node.
    """
    def __getitem__(self, id):
        """
        Provides access to nodes by their ids.

        If node is not stored in the cache, then parsing exception is
        raised.
        """
        if id in self:
            return super(NodeCache, self).__getitem__(id)
        else:
            raise ParseError('Id "%s" is not defined' % id)


    def __setitem__(self, id, node):
        """
        Store node by its id in cache. If there is a node already stored
        for given id, then ParseError error is raised.
        """
        if id in self:
            raise ParseError('Id "%s" is already defined' % id)
        else:
            super(NodeCache, self).__setitem__(id, node)



def name_dequote(n):
    """
    Remove quotation from a string.
    """
    n = n[1:-1]
    n = n.replace(r'\"', '"')
    n = n.replace(r"\'", "'")
    n = n.replace('\\\\', '\\')
    n = n.replace(r'\#', '#')
    return n




###
### expr ::= fdifacedep
### expr ::= assembly
###
RE_NAME = r""""(([^"]|\")+)"|'(([^']|\')+)'"""
RE_ATTRIBUTE = r'^\s+::?\s*[^:](\w+|\[(\w+|\w+\.\.\w+)\])\s*($|:.+?$|=.+?$|\[(\w+|\w+\.\.\w+)\]$)'
RE_ASSOCIATION_END = re.compile(r"""(?P<name>\w+)?\s* # attr name is optional
    ($
        | \[(?P<mult>\w+|\w+\.\.\w+)\] # multiplicity, i.e. [0], [n], [n..m]
    )
""", re.VERBOSE)



def _diagram():
    ast = self.ast = Diagram()
    ast.cache = NodeCache()
    ast.cache[ast.id] = self.ast

def p_fdiface(self, args):
    """
    fdiface ::= FDIFACE SPACE NAME
    fdiface ::= NAME SPACE FDIFACE
    """
    self._trim(args)
    id = None
    name = args[0].value
    symbol = args[1].value
    if args[0].type == 'FDIFACE':
        symbol, name = name, symbol
    n = IElement('fdiface', name)
    n.data['symbol'] = symbol
    n.data['dependency'] = None
    n.data['assembly'] = None
    n.data['lines'] = []
    self.ast.cache[n.id] = n

    self._set_parent('', n)
    return n


def _line(self, cls, tail, head, stereotypes=None, data=None):

    if data is None:
        data = {}
    if stereotypes is None:
        stereotypes = ()

    line = Line(cls, tail, head, data=data)

    line.stereotypes.extend(stereotypes)

    self._set_parent('', line)
    self.ast.cache[line.id] = line
    return line


def p_assembly(self, args):
    """
    assembly ::= ID SPACE fdiface SPACE ID
    assembly ::= ID SPACE assembly
    assembly ::= assembly SPACE ID
    """
    self._trim(args)
    error_fmt = 'Invalid id "%s" - component assembly allowed' \
            ' between components only'

    if len(args) == 3:
        id1 = args[0].value
        iface = args[1]
        id2 = args[2].value

        n1 = self.ast.cache[id1]
        n2 = self.ast.cache[id2]

        if n1.cls != 'component':
            raise UMLError(error_fmt % n1.id)
        if n2.cls != 'component':
            raise UMLError(error_fmt % n2.id)

        c1 = self._line('connector', n1, iface)
        c2 = self._line('connector', iface, n2)
        n = IElement('assembly')
        n.data['interface'] = iface
        iface.data['assembly'] = n
        iface.data['lines'].extend((c1, c2))
        return n
    else:
        if args[0].type == 'ID':
            n = self.ast.cache[args[0].value]
            assembly = args[1]
            tail = n
            iface = head = assembly.data['interface']
        else:
            assembly = args[0]
            n = self.ast.cache[args[1].value]
            iface = tail = assembly.data['interface']
            head = n

        if n.cls != 'component':
            raise UMLError(error_fmt % n.id)

        c = self._line('connector', tail, head)
        iface.data['lines'].append(c)
        return assembly


def p_fdifacedep(self, args):
    """
    fdifacedep ::= ID SPACE fdiface
    fdifacedep ::= fdiface SPACE ID
    """
    self._trim(args)
#        print 'iface:', args[0].value, args[1].value, args[2].value

    if args[0].type == 'ID':
        id = args[0].value
        iface = args[1]
        tail = iface
        head = self.ast.cache[id]
    else:
        iface = args[0]
        id = args[1].value
        tail = self.ast.cache[id]
        head = iface

    # truth matrix for dependency type
    tmatrix = {
        (True,  'o)'): 'realize',   # id--o)
        (True,  '(o'): 'use',       # id--(o
        (False, 'o)'): 'use',       # o)--id
        (False, '(o'): 'realize',   # (o--id
    }
    
    tid = args[0].type == 'ID'
    s = tmatrix[(tid, iface.data['symbol'])]

    n = self._line('dependency', tail, head, stereotypes=[s])

    # link dependency and interface
    n.data['supplier'] = iface
    iface.data['dependency'] = n
    iface.data['lines'].append(n)
    return n


def _feature(self, feature, value, title=False):
    """
    Create feature node. 

    :Parameters:
     feature
        Feature type, i.e. attribute, operation.
     value
        Name assigned to feature node.
     title
        If ``True`` then feature is title of features to follow, i.e.
        stereotype name of stereotype attributes.
    """
    indent, txt = value.split(':', 1)
    if title:
        txt = txt[:-1] # get rid of ending ':' from title
    txt = txt.strip()

    parent = self._istack[-1][1]

    # special treatment for an association
    if parent.cls == 'association':
        is_head = value.strip().startswith('::')

        if parent.data['tail'][1] is None and not is_head:
            end = 'tail'
        elif parent.data['head'][1] is None:
            end = 'head'
        else:
            raise UMLError('Too many association ends')

        et = parent.data[end][-1]
        mre = RE_ASSOCIATION_END.search(txt)
        constaint = None
        name, mult = mre.group('name', 'mult')
        if name is None:
            name = ''
        parent.data[end] = (constaint, name, mult, et)
    else:
        n = Feature(feature)
        n.name = txt
        self._set_parent(indent, n)
        return n



class List(list):
    """
    Named list of parsed items.
    """
    def __init__(self, name):
        self.name = name


    def __repr__(self):
        return '{}:{}'.format(self.name, super(List, self).__repr__())



def f_list(name):
    """
    Create a named list of parsed items.

    :Parameters:
     name
        Name of a list.
    """
    def f(args):
        l = List(name)
        l.extend(args)
        return l
    return f


def f_named(cls):
    """
    Factory to create named element.
    """
    def f(args):
        log.debug('named({}): {}'.format(cls, args))
        stereotypes = []
        data = {}

        if isinstance(args[2], List) and args[2].name == 'stereotypes':
            stereotypes.extend(args[2])
            del args[2]

        if isinstance(args[-1], List) and args[-1].name == 'stattrs':
            data['stattrs'] = list(args[-1])
            del args[-1]

        if isinstance(args[-1], List) and args[-1].name == 'operations':
            data['operations'] = list(args[-1])
            del args[-1]

        if isinstance(args[-1], List) and args[-1].name == 'attributes':
            data['attributes'] = list(args[-1])
            del args[-1]

        c, id, name = args
        name = name_dequote(name)

        if c in KEYWORDS:
            stereotypes.insert(0, c)

        n = cls(cls=c, id=id, stereotypes=stereotypes, name=name, data=data)
        __cache[n.id] = n
        return n
    return f


def f_packaging(args):
    """
    Factory to create packaging element.
    """
    log.debug('packaging {}'.format(args))
    parent, *children = args
    parent.children = [k[0] for k in children if k]
    for k in parent.children:
        k.parent = parent
    return parent


def _relationship(cls, tail, head, stereotypes=None, name=None, data=None):
    """
    Factory to create a relationship.
    """
    return Relationship(cls,
            __cache[tail], __cache[head],
            stereotypes=stereotypes,
            name=name,
            data=data)


def f_association(args):
    """
    Factory to create an association.
    """
    log.debug('association {}'.format(args))

    stereotypes = []
    tail_attr = None
    head_attr = None

    if isinstance(args[2], list):
        stereotypes.extend(args[2])
        del args[2]

    if (isinstance(args[-1], Attribute) or args[-1] is None) \
            and (isinstance(args[-2], Attribute) or args[-2] is None):
        head_attr = args[-1]
        del args[-1]

    if isinstance(args[-1], Attribute) or args[-1] is None:
        tail_attr = args[-1]
        del args[-1]

    name = None
    if len(args) == 4:
        name = name_dequote(args[2])
        del args[2]

    assert len(args) == 3
    #assert args[0].type == 'ID' and args[2].type == 'ID'

    AEND = {
        'x': 'none',
        'O': 'shared',
        '*': 'composite',
        '<': 'navigable',
        '>': 'navigable',
        '=': 'unknown',
    }
    t, h = __cache[args[0]], __cache[args[2]]
    v = args[1]
    data = {
        'name': name,
        'tail': (None, tail_attr, AEND[v[0]]),
        'head': (None, head_attr, AEND[v[-1]]),
        'direction': h if '=>=' in v \
                else t if '=<=' in v \
                else None,
    }
    e = _relationship('association', args[0], args[-1], stereotypes=stereotypes,
            name=name, data=data)

    t = e.tail.cls, e.head.cls
    if t == ('stereotype', 'metaclass') or t == ('metaclass', 'stereotype'):
        e.cls = 'extension'

    return e


def f_dependency(args):
    """
    Factory to create dependency relationship.
    """
    log.debug(args)
    TYPE = {
        'u': 'use',
        'r': 'realization',
        'i': 'import/include', # only between packages or use cases
        'm': 'merge',  # only between packages
        'e': 'extend', # only between use cases
    }
    v = args[1]
    dt = v[1] # dependency type

    s = TYPE.get(dt) # get default stereotype
    if s:
        stereotypes = [s]
    else:
        stereotypes = []
    if len(args) == 4:
        stereotypes.extend(args[2])
        del args[2]

    #assert args[0].type == 'ID' and args[2].type == 'ID'

    e = _relationship('dependency', args[0], args[-1], stereotypes=stereotypes)
    e.data['supplier'] = e.tail if v[0] == '<' else e.head

    if dt and dt in 'ime':
        t = e.tail.cls, e.head.cls
        t_p = 'package', 'package'
        t_u = 'usecase', 'usecase'

        # fix the stereotype
        if dt == 'i' and t == t_p:
            e.stereotypes[0] = 'import'
        elif dt == 'i' and t == t_u:
            e.stereotypes[0] = 'include'

        if dt == 'i' and (t != t_p and t != t_u):
            raise UMLError('Dependency -i> (package import or use case' \
                ' inclusion) can be specified only' \
                ' between two packages or two use cases')
        elif dt == 'm' and t != t_p:
            raise UMLError('Dependency -m> (package merge) can be' \
                ' specified only between two packages')
        elif dt == 'e' and t != t_u:
            raise UMLError('Dependency -e> (use case extension) can be' \
                ' specified only between two use cases')

    return e


def f_generalization(args):
    """
    Factory to create generalization relationship.
    """
    log.debug('generalization {}'.format(args))
    v = args[1]
    n = _relationship('generalization', args[0], args[-1])
    n.data['supplier'] = n.tail if v == '<=' else n.head
    return n


def f_commentline(args):
    """
    Factory to create comment line relationship.
    """
    log.debug('commentline {}'.format(args))
    n = _relationship('commentline', args[0], args[-1])
    # tail or head shall be comment
    tail, head = n.tail, n.head
    if not (tail.cls == 'comment') ^ (head.cls == 'comment'):
        raise UMLError('One of comment line ends shall be comment')
    return n


def f_mult(args):
    """
    Factory to create attribute multiplicity.
    """
    log.debug('multiplicity {}'.format(args))
    lower = args[0]
    upper = None if len(args) == 1 else args[1]
    return Mult(lower, upper)


def f_attribute(args):
    """
    Factory to create an attribute.
    """
    log.debug('attribute {}'.format(args))
    attr = None
    if len(args) > 0:
        name = None
        atype = None
        value = None
        mult = None

        if not isinstance(args[0], Mult):
            name = args[0]
            del args[0]

        for a in args:
            if isinstance(a, Mult):
                mult = a
            elif a[0] == ':':
                atype = a[1:].strip()
            elif a[0] == '=':
                value = a[1:].strip()

        attr = Attribute(name, atype, value, mult)
    return attr


def f_operation(args):
    """
    Factory to create an operation.
    """
    log.debug('operation {}'.format(args))
    return Operation(args[0].strip())


def f_layout(args):
    """
    Factory to create diagram alignment information.
    """
    log.debug('layout {}'.format(args))
    s = Section('layout')
    for p in args[1:]:
        a = Align(p[0])
        for id in p[1:]:
            a.nodes.append(__cache[id])
        s.data.append(a)
    return s


def create_parser():
    global __cache
    __cache = {}

    Token = P.Token
    Or = P.Or
    Literal = P.Literal

    def joinl(literals, f=Or):
        return Token(f(*(Literal(t) for t in literals)))

    space =  ~Token(' +')
    #string = Token(r""""(([^"]|\")+)"|'(([^']|\')+)'""")
    #string = ~Token('"') + Token('[^"]+') + ~Token('"')
    string = Token('"[^"]+"') | Token("'[^']+'")
    id = Token('[a-zA-Z][a-zA-Z0-9_]*')
    stereotype = Token('[a-zA-Z0-9]+')
    stereotypes = ~Token('<<') & space[0:1] \
        & stereotype \
        & (~Token(' *, *') & stereotype)[0:] \
        & space[0:1] & ~Token('>>') > f_list('stereotypes')
    eparams = space & id & (space & stereotypes)[0:1] & space & string

    nelement = joinl(NELEMENTS) & eparams
    pelement = joinl(PELEMENTS) & eparams

    association = id & space \
            & Token('[xO\*<]?=[<>]?=[xO\*>]?') \
            & (space & stereotypes)[0:1] \
            & (space & string)[0:1] \
            & space & id

    dependency = id & space \
            & (Token('\-[urime]?>') | Token('<[urime]?\-')) \
            & (space & stereotypes)[0:1] & space & id > f_dependency

    generalization = id & space \
            & (Token('<=') | Token('=>')) \
            & space & id > f_generalization

    commentline = id & space & Token('\-\-') & space & id > f_commentline

    relationship = dependency | generalization | commentline

    mnum = Token('[a-zA-Z0-9\*]+')
    aword = Token('[a-zA-Z0-9\-]+')
    mult = ~Token('\[') & mnum \
            & (space[0:1] & ~Token('\.\.') & space[0:1] & mnum)[0:1] \
            & ~Token('\]')

    aend = ~Token(':') & (space[0:1] & aword)[0:1] \
            & (space[0:1] & mult > f_mult)[0:1] > f_attribute

    attribute = ~Token(':') & space[0:1] \
            & aword \
            & (space[0:1] & Token(':') + space[0:1] + aword)[0:1] \
            & (space[0:1] & Token('=[^=><]+'))[0:1] \
            & (space[0:1] & mult > f_mult)[0:1] \
            > f_attribute
    operation = ~Token(':') & space \
            & Token('[a-zA-Z_][a-zA-Z0-9_]*\(.*\).*') > f_operation
    stattrs = P.Line(~Token(':') & space & ~Token('<<') \
                & stereotype & ~Token('>>') & space & ~Token(':')) \
            & P.Block(P.Line(attribute)[1:] > f_list('attributes')) > tuple

    features = (P.Line(attribute)[0:] > f_list('attributes')) \
            & (P.Line(operation)[0:] > f_list('operations')) \
            & (stattrs[0:] > f_list('stattrs'))

    layout = ~Token(':') & Token('layout') & ~Token(':')
    align  = (Token('top') | Token('right') | Token('bottom') \
                | Token('left') | Token('middle') | Token('center')) \
            & ~ Token(':') \
            & space[0:] & id & (space & id)[1:] > list

    statement = P.Delayed()

    empty = P.Line(P.Empty(), indent=False)
    comment = P.Line(Token('#.*'), indent=False)
    rline = P.Line(relationship)
    nblock = P.Line(nelement) & P.Block(features)[0:1] > f_named(Element)
    pblock = P.Line(pelement) & P.Block(features)[0:1] > f_named(PackagingElement)

    block = (P.Line(pelement) > f_named(PackagingElement)) \
            & P.Block(statement[1:]) > f_packaging
    ablock = P.Line(association) \
            & P.Block(P.Line(aend))[0:2] > f_association

    lblock = P.Line(layout) & P.Block(P.Line(align)[1:]) > f_layout

    statement += (block | ablock | nblock | pblock | lblock \
            | rline | ~comment | empty) > list
    program = statement[:]

    program.config.lines(block_policy=P.constant_indent(4))
    return program


__parser = create_parser()


def parse(f):
    """
    :Parameters:
     f
        File to load diagram description from.
    """
    try:
        if isinstance(f, str):
            nodes = __parser.parse(f)
        else:
            # parse_file is causing problems at the moment
            nodes = __parser.parse(''.join(f))
    except P.FullFirstMatchException as ex:
        raise ParseError(str(ex))
    except P.RuntimeLexerError as ex:
        raise ParseError(str(ex))

    return Diagram((k[0] for k in nodes if k != []))


# vim: sw=4:et:ai
