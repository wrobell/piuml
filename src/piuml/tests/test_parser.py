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


    def test_dependency_stereotypes(self):
        """Test dependency stereotype parsing
        """
        f = StringIO("""
class a 'A' <<aaa>>
class b 'B' <<bbb>>

a -> <<test>> b
""")
        ast = load(f)
        deps = [n for n in unwind(ast) if n.element == 'dependency']
        dep = deps[0]
        self.assertEquals(['test'], dep.stereotypes)


    def test_association_stereotypes(self):
        """Test association stereotype parsing
        """
        f = StringIO("""
class a 'A' <<aaa>>
class b 'B' <<bbb>>

a == 'a name' <<t1, t2>> b
""")
        ast = load(f)
        assocs = [n for n in unwind(ast) if n.element == 'association']
        assoc = assocs[0]
        self.assertEquals('a name', assoc.name)
        self.assertEquals(['t1', 't2'], assoc.stereotypes)



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


    def test_association_ends(self):
        """Test adding an association end
        """
        f = StringIO("""
class c1 "A"
class c2 "B"

c1 == c2
    : one [0..1]
    : two
""")
        ast = load(f)
        ast.id = 'diagram'
        assocs = [n for n in unwind(ast) if n.element == 'association']
        self.assertEquals(1, len(assocs))

        assoc = assocs[0]
        self.assertEquals(0, len(assoc))
        self.assertEquals('one', assoc.data['tail'][1])
        self.assertEquals('0..1', assoc.data['tail'][2])
        self.assertEquals('two', assoc.data['head'][1])
        self.assertEquals(None, assoc.data['head'][2])


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


    def test_association_name(self):
        """Test association name
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
""")
        ast = load(f)
        names = [n.name for n in unwind(ast) if n.element == 'association']
        self.assertEquals(['An association'], names)


    def test_association_ends_error(self):
        """Test association with too many ends
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

c1 =>= c2
    : a
    : b
    : c
""")
        self.assertRaises(UMLError, load, f)


    def test_association_head_only(self):
        """Test association with association end at head only
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
    :: head [0..n]
""")
        ast = load(f)
        assocs = [n for n in unwind(ast) if n.element == 'association']
        self.assertEquals(['An association'], [n.name for n in assocs])
        assoc = assocs[0]
        self.assertEquals(0, len(assoc))
        self.assertEquals((None, None, None, 'unknown'), assoc.data['tail'])
        self.assertEquals((None, 'head', '0..n', 'unknown'), assoc.data['head'])
       

# vim: sw=4:et:ai
