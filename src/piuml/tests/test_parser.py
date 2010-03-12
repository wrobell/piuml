"""
piUML language parser tests.
"""

import unittest
from cStringIO import StringIO

from piuml.parser import load, ParseError, st_parse, unwind


class GroupingTestCase(unittest.TestCase):
    """
    Element grouping test case.
    """
    def test_simple(self):
        """Test simple grouping
        """
        f = StringIO("""
component c1 "A"
component c2 "B"
    class cls1 "B1"
""")
        ast = load(f)
        ast.id = 'diagram'
        data = dict((n.id, n.parent.id) for n in unwind(ast) if n.parent)
        self.assertEquals('diagram', data['c1'])
        self.assertEquals('diagram', data['c2'])
        self.assertEquals('c2', data['cls1'])


    def test_complex(self):
        """Test complex grouping
        """
        f = StringIO("""
component c1 "A"
component c2 "B"
    class cls1 "B1"
    class cls2 "B2"
        class cls3 "B21"
        class cls4 "B22"
            class cls5 "B221"
    class cls6 "B3"
        class cls7 "B23"
    class cls8 "B4"
class cls9 "C"
""")

        ast = load(f)
        ast.id = 'diagram'

        data = dict((n.id, n.parent.id) for n in unwind(ast) if n.parent)

        self.assertEquals('diagram', data['c1'])
        self.assertEquals('diagram', data['c2'])
        self.assertEquals('diagram', data['cls9'])

        self.assertEquals('c2', data['cls1'])
        self.assertEquals('c2', data['cls2'])

        self.assertEquals('cls2', data['cls3'])
        self.assertEquals('cls2', data['cls4'])

        self.assertEquals('cls4', data['cls5'])

        self.assertEquals('c2', data['cls6'])
        self.assertEquals('cls6', data['cls7'])
        self.assertEquals('c2', data['cls8'])


    def test_wrong_indentation(self):
        """Test inconsistent indentation
        """
        f = StringIO("""
component c1 "A"
component c2 "B"
    class cls1 "B1"
  class cls2 "B1"
""")
        self.assertRaises(ParseError, load, f)



class StereotypesTestCase(unittest.TestCase):
    def test_single(self):
        """Test single stereotype parsing
        """
        self.assertEquals(('test',), st_parse('<<test>>'))
        self.assertEquals(('test',), st_parse('<< test >>'))


    def test_multiple(self):
        """Test multiple stereotypes parsing
        """
        self.assertEquals(('t1', 't2'), st_parse('<<t1, t2>>'))
        self.assertEquals(('t1', 't2'), st_parse('<<t1,t2>>'))
        self.assertEquals(('t1', 't2'), st_parse('<< t1,t2>>'))
        self.assertEquals(('t1', 't2'), st_parse('<< t1   ,   t2   >>'))


    def test_st_parsing(self):
        """Test stereotype parsing
        """
        f = StringIO('component a "A" <<test>>')
        ast = load(f)
        self.assertEquals(['component', 'test'], ast[0].stereotypes)

        f = StringIO('component a "A" <<t1, t2>>')
        ast = load(f)
        self.assertEquals(['component', 't1', 't2'], ast[0].stereotypes)

