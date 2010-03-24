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

from spark import GenericScanner, GenericParser, GenericASTTraversal

import re
from uuid import uuid4 as uuid
from collections import namedtuple


class ParseError(Exception):
    """
    piUML language parsing exception.
    """
    def __init__(self, msg):
        super(ParseError, self).__init__(msg)
        global filename, lineno
        self.msg = msg
        self.filename = filename
        self.lineno = lineno


    def __str__(self):
        if self.filename and self.lineno:
            return '%s:%d:%s' % (self.filename, self.lineno, self.msg)
        else:
            return super(ParseError, self).__str__()



class UMLError(ParseError):
    """
    UML semantics error. Raised when some UML semantics error is
    discovered.
    """



class Token(object):
    """
    piUML language token data with type and value.

    :Attributes:
     type
        Token type.
     value
        Token value.
    """
    def __init__(self, type, value):
        self.type  = type
        self.value = value


    def __cmp__(self, o):
        return cmp(self.type, o)


    def __str__(self):
        return self.value

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



class NodeCache(dict):
    """
    Cache of nodes.

    A node is accessed by its id.
    """
    def __getitem__(self, key):
        """
        Provides access to nodes by their ids.

        If node is not stored in the cache, then parsing exception is
        raised.
        """
        if key not in self:
            raise ParseError('Id "%s" is not defined' % key)
        else:
            return super(NodeCache, self).__getitem__(key)



def unwind(node):
    yield node
    for i in node:
        for j in unwind(i):
            yield j


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


def st_parse(stereotype):
    """
    Parse stereotypes from a string.
    """
    stereotype = stereotype.replace('<<', '').replace('>>', '')
    return tuple(s.strip() for s in stereotype.split(','))


# elements
ELEMENTS = ('artifact', 'comment', 'class', 'component', 'device',
        'interface', 'node')

RE_NAME = r""""(([^"]|\")+)"|'(([^']|\')+)'"""
RE_ID = r'(?!%s)\b[a-zA-Z_]\w*\b' % '|'.join(r'%s\b' % s for s in ELEMENTS)
RE_ELEMENT = r'^[ ]*(%s)' % '|'.join(r'\b%s\b' % s for s in ELEMENTS)
RE_COMMENT = r'\s*(?<!\\)\#.*'
RE_STEREOTYPE = r'(?<!:[ ])<<[ ]*\w[\w ,]*>>'
RE_ATTRIBUTE = r'^\s+::?\s*[^:](\w+|\[(\w+|\w+\.\.\w+)\])\s*($|:.+?$|=.+?$|\[(\w+|\w+\.\.\w+)\]$)'
RE_OPERATION = r'^\s+:\s*\w\w*\(.*\).*$'
RE_STATTRIBUTES = r'^\.\s+:\s*<<\w+>>\s*$'

RE_ASSOCIATION_END = re.compile(r"""(?P<name>\w+)?\s* # attr name is optional
    ($
        | \[(?P<mult>\w+|\w+\.\.\w+)\] # multiplicity, i.e. [0], [n], [n..m]
    )
""", re.VERBOSE)

TOKENS = {
    'ID': RE_ID,
    'NAME': (RE_NAME, name_dequote),
    'STEREOTYPE': RE_STEREOTYPE,
    'COMMENT': RE_COMMENT,
    'ELEMENT': RE_ELEMENT,
    'FDIFACE': r'o\)|\(o', # folded interface
    'ASSOCIATION': r'[xO*<]?=(<|>)?=[xO*>]?',
    'DEPENDENCY': r'<[ur]?-|-[ur]?>',
    'GENERALIZATION': r'(<=)|(=>)',
    'COMMENTLINE': r'--',
    'ATTRIBUTE': RE_ATTRIBUTE,
    'OPERATION': RE_OPERATION,
    'STATTRIBUTES': RE_STATTRIBUTES,
    'SPACE': r'[ 	]+',
}


class piUMLScanner(GenericScanner):
    """
    piUML language scanner.
    
    Divides lines into tokens ready for more advanced interpretation.
    """
    def __init__(self):
        for name, data in TOKENS.items():
            if isinstance(data, basestring):
                f = lambda d: d
            else:
                data, f = data
            self._create_token(name, data, f)
        GenericScanner.__init__(self)


    def _create_token(self, name, regex, f):
        def tokenf(self, value):
            t = Token(name, f(value))
            self.rv.append(t)
        tokenf.__doc__ = regex
        setattr(self.__class__, 't_' + name, tokenf)


    def tokenize(self, line):
        """
        Create tokens from string.

        :Parameters:
         line
            String to scan.
        """
        self.rv = []
        GenericScanner.tokenize(self, line)
        return self.rv


    def error(self, value, pos):
        raise ParseError('Syntax error near "%s"' % value)


    def t_default(self, value):
        r'(.|\n)+'
        raise ParseError('Syntax error near "%s"' % value)



class piUMLParser(GenericParser):
    """
    piUML parser.

    :Attributes:
     ast
        Root node of the parsed tree.
     nodes
        All nodes stored by their id.
     _istack
        Element grouping stack.
    """
    def __init__(self):
        GenericParser.__init__(self, 'expr')
        self.ast = Node('diagram', 'diagram')
        self.nodes = NodeCache()

        # grouping with indentation is supported with stack structure
        self._istack = []
        self._istack.append((0, self.ast))


    def error(self, token):
        raise ParseError('Syntax error near "%s"' % token)


    def p_expr(self, args):
        """
        expr ::= expr comment
        expr ::= stelement
        expr ::= element
        expr ::= attribute
        expr ::= operation
        expr ::= stattributes
        expr ::= association
        expr ::= generalization
        expr ::= commentline
        expr ::= dependency
        expr ::= fdifacedep
        expr ::= assembly
        expr ::= comment
        expr ::= empty
        """
        return args[0]


    def p_element(self, args):
        """
        element ::= ELEMENT SPACE ID SPACE NAME
        """
        STEREOTYPES = {
            'device': 'device',
            'component': 'component',
            'artifact': 'artifact',
            'interface': 'interface',
        }
        self._trim(args)

        element = args[0].value.strip()
        indent = args[0].value.split(element)[0]
        id = args[1].value
        name = args[2].value
        stereotype = STEREOTYPES.get(element)

        n = Node('element', element, name=name)
        n.id = id
        if stereotype:
            n.stereotypes.append(stereotype)

        self.nodes[id] = n
        self._set_parent(indent, n)

        return n


    def _set_parent(self, indent, n):
        # identify diagram level on which grouping happens
        level = len(indent)

        # find and set parent using the indentation stack
        istack =  self._istack
        i = istack[-1][0]
        if i == level:
            # last node cannot group anymore, replace it with current one
            if len(istack) > 1:
                istack.pop()
            istack.append((level, n))
        elif i < level:
            istack.append((level, n))
        else: # i > level
            while i > level:
                i = istack.pop()[0]
            if i < level:
                raise ParseError('Inconsistent indentation')
            istack.append((level, n))

        n.parent = parent = istack[-2][1]
        parent.append(n)


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
        n = Node('ielement', 'fdiface', name)
        n.data['symbol'] = symbol
        n.data['dependency'] = None
        n.data['assembly'] = None
        n.data['lines'] = []
        self.nodes[n.id] = n

        self._set_parent('', n)
        return n


    def p_stelement(self, args):
        """
        stelement ::= element SPACE STEREOTYPE
        """
        n = args[0]
        n.stereotypes.extend(st_parse(args[2].value))
        return n


    def _trim(self, args):
        """
        Remove whitespace from arguments.
        """
        # remove spaces
        t = len(args)
        for i, a in enumerate(reversed(list(args))):
            if a.type == 'SPACE':
                del args[t - i -1]


    def _line(self, element, tail, head, stereotypes=None, data=None):

        if data is None:
            data = {}
        if stereotypes is None:
            stereotypes = ()

        n = Edge(element, element, tail, head, data=data)

        n.stereotypes.extend(stereotypes)

        self.ast.append(n)
        self._istack[-1] = (0, n)
        self.nodes[id] = n
        return n


    def _get_ends(self, args):
        nodes = self.nodes
        head = nodes[args[0].value]
        tail = nodes[args[2].value]
        return head, tail


    def p_association(self, args):
        """
        association ::= ID SPACE ASSOCIATION SPACE ID
        association ::= ID SPACE ASSOCIATION SPACE NAME SPACE ID
        association ::= ID SPACE ASSOCIATION SPACE NAME SPACE STEREOTYPE SPACE ID
        """
        self._trim(args)

        name = None
        if args[2].type == 'NAME':
            name = args[2].value
            del args[2]

        stereotypes = []
        if args[2].type == 'STEREOTYPE':
            stereotypes.extend(st_parse(args[2].value))
            del args[2]

        assert args[0].type == 'ID' and args[2].type == 'ID'

        AEND = {
            'x': 'none',
            'O': 'shared',
            '*': 'composite',
            '<': 'navigable',
            '>': 'navigable',
            '=': 'unknown',
        }
        v = args[1].value
        data = {
            'name': name,
            'tail': (None, None, None, AEND[v[0]]),
            'head': (None, None, None, AEND[v[-1]]),
            'direction': 'head' if '=>=' in v \
                    else 'tail' if '=<=' in v \
                    else None,
        }
        e = self._line('association',
                *self._get_ends(args),
                data=data,
                stereotypes=stereotypes)
        if name:
            e.name = name

        # change default style for an association
        e.style.padding = Area(3, 18, 3, 18)

        return e


    def p_dependency(self, args):
        """
        dependency ::= ID SPACE DEPENDENCY SPACE ID
        dependency ::= ID SPACE DEPENDENCY SPACE STEREOTYPE SPACE ID
        """
        self._trim(args)
        TYPE = {
            'u': 'use',
            'r': 'realize',
        }
        v = args[1].value

        s = TYPE.get(v[1]) # get defaul stereotype
        if s:
            stereotypes = [s]
        else:
            stereotypes = []
        if args[2].type == 'STEREOTYPE':
            stereotypes.extend(st_parse(args[2].value))
            del args[2]
        assert args[0].type == 'ID' and args[2].type == 'ID'
        n = self._line('dependency', *self._get_ends(args), stereotypes=stereotypes)
        n.data['supplier'] = n.tail if v[0] == '<' else n.head
        return n


    def p_generalization(self, args):
        """
        generalization ::= ID SPACE GENERALIZATION SPACE ID
        """
        self._trim(args)
        v = args[1].value
        n = self._line('generalization', *self._get_ends(args))
        n.data['super'] = n.tail if v == '<=' else n.head
        return n


    def p_commentline(self, args):
        """
        commentline ::= ID SPACE COMMENTLINE SPACE ID
        """
        self._trim(args)
        tail, head = self._get_ends(args)
        # one of ends shall be comment
        if not (tail.element == 'comment') ^ (head.element == 'comment'):
            raise UMLError('One of comment line ends shall be comment')
        n = self._line('commentline', tail, head)
        return n


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

            n1 = self.nodes[id1]
            n2 = self.nodes[id2]

            if n1.element != 'component':
                raise UMLError(error_fmt % n1.id)
            if n2.element != 'component':
                raise UMLError(error_fmt % n2.id)

            c1 = self._line('connector', n1, iface)
            c2 = self._line('connector', iface, n2)
            n = Node('connector', 'assembly')
            n.data['interface'] = iface
            iface.data['assembly'] = n
            iface.data['lines'].extend((c1, c2))
            return n
        else:
            if args[0].type == 'ID':
                n = self.nodes[args[0].value]
                assembly = args[1]
                tail = n
                iface = head = assembly.data['interface']
            else:
                assembly = args[0]
                n = self.nodes[args[1].value]
                iface = tail = assembly.data['interface']
                head = n

            if n.element != 'component':
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
            head = self.nodes[id]
        else:
            iface = args[0]
            id = args[1].value
            tail = self.nodes[id]
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


    def _feature(self, feature, value):
        indent = value.split(':')[0]
        txt = value.strip()[1:].strip()

        parent = self._istack[-1][1]

        # special treatment for an association
        if parent.element == 'association':
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
            n = Node('feature', feature)
            n.name = txt
            self._set_parent(indent, n)
            return n


    def p_attribute(self, args):
        """
        attribute ::= ATTRIBUTE
        """
        return self._feature('attribute', args[0].value)


    def p_operation(self, args):
        """
        operation ::= OPERATION
        """
        return self._feature('operation', args[0].value)


    def p_stattributes(self, args):
        """
        stattributes ::= STATTRIBUTES
        """
        n = self._feature('stattributes', args[0].value[1:])
        n.name = st_parse(n.name)[0]
        return n


    def p_comment(self, args):
        """
        comment ::= COMMENT
        """
        return Node('comment', 'comment')


    def p_empty(self, args):
        """
        empty ::= EMPTY
        """
        return Node('empty', 'empty')



def load(f):
    """
    :Parameters:
     f
        File to load diagram data from.
    """
    global lineno, filename
    lineno = 0
    if hasattr(f, 'name'):
        filename = f.name
    else:
        filename = '-'

    scanner = piUMLScanner()
    parser = piUMLParser()

    for line in f:
        line = line.rstrip()
        lineno += 1
        if line:
            tokens = scanner.tokenize(line)
            parser.parse(tokens)
    return parser.ast


# vim: sw=4:et:ai
