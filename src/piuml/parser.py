from spark import GenericScanner, GenericParser, GenericASTTraversal

from uuid import uuid4 as uuid
from collections import namedtuple


class ParseError(Exception):
    """
    Parsing exception. Raised when input data cannot be parse or when
    created gallery data model is inconsistent.
    """
    def __init__(self, message, filename = None, lineno = None):
        super(ParseError, self).__init__()
        self.message = message
        self.filename = filename
        self.lineno = lineno


    def __str__(self):
        if self.filename and self.lineno:
            return '%s:%d:%s' % (self.filename, self.lineno, self.message)
        else:
            return super(ParseError, self).__str__()

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
        self.padding = Area(5, 10, 20, 10)
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
        self.id = uuid()
        self.name = name
        self.stereotypes = []
        self.data = data if data else {}
        self.style = Style()



class Edge(Node):
    """
    Edge between nodes like association, dependency, comment line, etc.

    :Attributes:
     tail
        Tail node.
     head
        Head node. 
    """
    def __init__(self, type, element, head, tail, name='', data=[]):
        super(Edge, self).__init__(type, element, name, data)
        self.tail = tail
        self.head = head


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


ELEMENTS = 'class', 'node', 'device', 'component', 'artifact'

RE_NAME = r""""(([^"]|\")+)"|'(([^']|\')+)'"""
RE_ID = r'(?!%s)\b[a-zA-Z_]\w*\b' % '|'.join(r'%s\b' % s for s in ELEMENTS)
RE_ELEMENT = r'^[ ]*(%s)' % '|'.join(ELEMENTS)
RE_COMMENT = r'\s*(?<!\\)\#.*'
RE_STEREOTYPE = r'<<[ ]*\w[\w ,]*>>'

TOKENS = {
    'ID': RE_ID,
    'NAME': (RE_NAME, name_dequote),
    'COMMENT': RE_COMMENT,
    'ELEMENT': RE_ELEMENT,
    'ASSOCIATION': r'[xO*<]?==[xO*>]?',
    'DEPENDENCY': r'<[ur]?-|-[ur]?>',
    'GENERALIZATION': r'(<=)|(=>)',
    'STEREOTYPE': RE_STEREOTYPE,
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
        global filename, lineno
        raise ParseError('syntax error', filename, lineno)


    def t_default(self, value):
        r'(.|\n)+'
        global filename, lineno
        if 'filename' in globals() and 'lineno' in globals():
            raise ParseError('syntax error near "%s"' % value, filename, lineno)
        else:
            raise ParseError('syntax error, invalid token %s' % value)



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
        self.nodes = {}

        # grouping with indentation is supported with stack structure
        self._istack = []
        self._istack.append((0, self.ast))


    def error(self, token):
        global filename, lineno
        raise ParseError('syntax error %s %s' % (token, token.type), filename, lineno)


    def p_expr(self, args):
        """
        expr ::= expr comment
        expr ::= selement
        expr ::= element
        expr ::= association
        expr ::= generalization
        expr ::= dependency
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
                global filename, lineno
                raise ParseError('Inconsistent indentation', filename, lineno)
            istack.append((level, n))

        n.parent = parent = istack[-2][1]
        parent.append(n)

        return n


    def p_selement(self, args):
        """
        selement ::= element SPACE STEREOTYPE
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


    def _line(self, element, args, stereotypes=None, data=None):

        if data is None:
            data = {}
        if stereotypes is None:
            stereotypes = ()

        tail = args[0].value
        head = args[2].value

        n = Edge(element, element, self.nodes[tail], self.nodes[head], data=data)

        n.stereotypes.extend(stereotypes)

        self.ast.append(n)
        self.nodes[id] = n
        return n


    def p_association(self, args):
        """
        association ::= ID SPACE ASSOCIATION SPACE ID
        """
        self._trim(args)
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
            'tail': AEND[v[0]],
            'head': AEND[v[-1]],
        }
        return self._line('association', args, data=data)


    def p_dependency(self, args):
        """
        dependency ::= ID SPACE DEPENDENCY SPACE ID
        dependency ::= ID SPACE DEPENDENCY SPACE ID SPACE STEREOTYPE
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
        if len(args) == 4:
            stereotypes.append(args[3].value)
        n = self._line('dependency', args, stereotypes=stereotypes)
        n.data['supplier'] = n.tail if v[0] == '<' else n.head
        return n


    def p_generalization(self, args):
        """
        generalization ::= ID SPACE GENERALIZATION SPACE ID
        """
        self._trim(args)
        v = args[1].value
        n = self._line('generalization', args)
        n.data['super'] = n.tail if v == '<=' else n.head
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
    :param: f
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
