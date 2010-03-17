"""
piUML language parser tests.
"""

import unittest
from cStringIO import StringIO

from piuml.parser import load, ParseError, UMLError, st_parse, unwind


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



class FeatureTestCase(unittest.TestCase):
    """
    Adding features (i.e. attributes) to elements.
    """
    def test_attribute(self):
        """Test adding an attribute
        """
        f = StringIO("""
class c1 "A"
    : x: int
    : y: int
""")
        ast = load(f)
        ast.id = 'diagram'
        data = dict((n.id, n) for n in unwind(ast))
        cls = data['c1']
        self.assertEquals(2, len(cls))
        self.assertEquals('x: int', cls[0].name)
        self.assertEquals('y: int', cls[1].name)



class GeneralLanguageTestCase(unittest.TestCase):
    """
    General piUML language tests.
    """
    def test_undefined_id(self):
        """Test an edge to an undefined id
        """
        f = StringIO("""
class c1 "Test1"
class c2 "Test2"
c1 -- cx
""")
        self.assertRaises(ParseError, load, f)



class UMLCheckTestCase(unittest.TestCase):
    """
    UML semantics test case.
    """
    def test_commentline(self):
        """Test comment line creation
        """
        f = StringIO("""
comment c1 "Test comment 1"
comment c2 "Test comment 2"
c1 -- c2
""")
        self.assertRaises(UMLError, load, f)

        f = StringIO("""
class c1 "TestClass1"
class c2 "TestClass2"
c1 -- c2
""")
        self.assertRaises(UMLError, load, f)


    def test_assembly(self):
        """Test component assembly creation
        """
        f = StringIO("""
component c "Component"
class cls "Class"
c o) "Iface" cls
""")
        self.assertRaises(UMLError, load, f)

        f = StringIO("""
component c1 "C1"
component c2 "C2"
component c3 "C3"
class cls "Class"
c1 c2 o) "A" c3 cls
""")
        self.assertRaises(UMLError, load, f)



class LinesTestCase(unittest.TestCase):
    def test_association_dir(self):
        """Test association direction
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"

c1 =>= c2
c2 =<= c3
c3 == c1
""")
        ast = load(f)
        dirs = [n.data['direction'] for n in unwind(ast) \
            if n.element == 'association']
        self.assertEquals(['head', 'tail', None], dirs)
       

