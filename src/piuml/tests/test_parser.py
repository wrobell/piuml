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
from io import StringIO

from piuml.parser import parse, ParseError, UMLError
from piuml.data import unwind


class PackagingTestCase(unittest.TestCase):
    """
    Element packaging test case.
    """
    def test_simple(self):
        """
        Test simple packaging
        """
        f = """
component c1 "A"
component c2 "B"
    class cls1 "B1"
"""
        n = parse(f)
        data = dict((k.id, k.parent.id) for k in unwind(n) if k.parent)
        self.assertEquals('diagram', data['c1'])
        self.assertEquals('diagram', data['c2'])
        self.assertEquals('c2', data['cls1'])


    def test_complex(self):
        """
        Test complex packaging
        """
        f = """
component c1 "A"
component c2 "B"
component c3 "C"
    class cls1 "B1"
    class cls2 "B2"
        class cls3 "B21"
        class cls4 "B22"
            class cls5 "B221"
    class cls6 "B3"
        class cls7 "B23"
    class cls8 "B4"
class cls9 "C"
"""

        n = parse(f)

        data = dict((k.id, k.parent.id) for k in unwind(n) if k.parent)

        self.assertEquals('diagram', data['c1'])
        self.assertEquals('diagram', data['c2'])
        self.assertEquals('diagram', data['c3'])
        self.assertEquals('diagram', data['cls9'])

        self.assertEquals('c3', data['cls1'])
        self.assertEquals('c3', data['cls2'])

        self.assertEquals('cls2', data['cls3'])
        self.assertEquals('cls2', data['cls4'])

        self.assertEquals('cls4', data['cls5'])

        self.assertEquals('c3', data['cls6'])
        self.assertEquals('cls6', data['cls7'])
        self.assertEquals('c3', data['cls8'])


    def test_wrong_indentation(self):
        """Test inconsistent indentation
        """
        f = """
component c1 "A"
component c2 "B"
    class cls1 "B1"
  artifact a1 "A1"
"""
        self.assertRaises(ParseError, parse, f)



class StereotypesTestCase(unittest.TestCase):
    def test_st_parsing(self):
        """
        Test stereotype parsing
        """
        f = 'component a <<test>> "A"'
        n = parse(f)
        self.assertEquals(['component', 'test'], n[0].stereotypes)

        f = 'component a <<t1, t2>> "A"'
        n = parse(f)
        self.assertEquals(['component', 't1', 't2'], n[0].stereotypes)


    def test_dependency_stereotypes(self):
        """Test dependency stereotype parsing
        """
        f = StringIO("""
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a -> <<test>> b
""")
        ast = parse(f)
        deps = [n for n in ast.unwind() if n.cls == 'dependency']
        dep = deps[0]
        self.assertEquals(['test'], dep.stereotypes)


    def test_association_stereotypes(self):
        """Test association stereotype parsing
        """
        f = StringIO("""
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a == <<t1, t2>> 'a name' b
""")
        ast = parse(f)
        assocs = [n for n in ast.unwind() if n.cls == 'association']
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
        ast = parse(f)
        ast.id = 'diagram'
        data = dict((n.id, n) for n in ast.unwind())
        cls = data['c1']
        self.assertEquals(2, len(cls))
        self.assertEquals('x: int', cls[0].name)
        self.assertEquals('y: int', cls[1].name)


    def test_st_attributes(self):
        """Test adding stereotype attributes
        """
        f = StringIO("""
class c1 "A"
    : <<tt>> :
        : x: int
        : y: int
""")
        ast = parse(f)
        cls = ast.cache['c1']
        self.assertEquals(1, len(cls))
        self.assertEquals(2, len(cls[0]))
        self.assertEquals('tt', cls[0].name)
        self.assertEquals('x: int', cls[0][0].name)
        self.assertEquals('y: int', cls[0][1].name)


    def test_st_attributes_with_packaging(self):
        """Test adding stereotype attributes with packaging
        """
        f = StringIO("""
class c1 'A'
    class c2 'B'
    : <<tt>> :
        : x: int
        : y: int
""")
        ast = parse(f)
        cls = ast.cache['c1']
        self.assertEquals(2, len(cls)) # stereotype <<tt>> attributes and inner class c2
        self.assertEquals(2, len(cls[1]))
        self.assertEquals('tt', cls[1].name)
        self.assertEquals('x: int', cls[1][0].name)
        self.assertEquals('y: int', cls[1][1].name)


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
        ast = parse(f)
        ast.id = 'diagram'
        assocs = [n for n in ast.unwind() if n.cls == 'association']
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
        self.assertRaises(ParseError, parse, f)


    def test_duplicate_id(self):
        """Test duplicate id specification
        """
        f = StringIO("""
class c1 "Test1"
class c1 "Test2" # note duplicated id
""")
        self.assertRaises(ParseError, parse, f)


    def test_line_interleave(self):
        """Test an edge to an undefined id
        """
        f = StringIO("""
class c1 "Test1"
    class c2 "Test2"

c1 == c2

class c3 "Test3"
    class c4 "Test4"

c2 == c3
""")
        ast = parse(f)
        data = [n.parent.type for n in ast.unwind() if n.cls == 'class']
        self.assertEquals(['diagram', 'element'] * 2, data)


    def test_invalid_layout_spec(self):
        """Test parsing of invalid layout specification
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

    center: c1 c2
""")
        self.assertRaises(ParseError, parse, f)




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
        self.assertRaises(UMLError, parse, f)

        f = StringIO("""
class c1 "TestClass1"
class c2 "TestClass2"
c1 -- c2
""")
        self.assertRaises(UMLError, parse, f)


    def test_assembly(self):
        """Test component assembly creation
        """
        f = StringIO("""
component c "Component"
class cls "Class"
c o) "Iface" cls
""")
        self.assertRaises(UMLError, parse, f)

        f = StringIO("""
component c1 "C1"
component c2 "C2"
component c3 "C3"
class cls "Class"
c1 c2 o) "A" c3 cls
""")
        self.assertRaises(UMLError, parse, f)



class LinesTestCase(unittest.TestCase):
    """
    Line elements tests.
    """
    def test_package_merge_import(self):
        """Test package merge and package import
        """
        f = StringIO("""
package p1 "P1"
package p2 "P2"

p1 -m> p2
p1 -i> p2
""")
        ast = parse(f)
        deps = [n for n in ast.unwind() if n.cls == 'dependency']
        self.assertEquals(['merge'], deps[0].stereotypes)
        self.assertEquals(['import'], deps[1].stereotypes)


    def test_package_merge_error(self):
        """Test package merge error
        """
        f = StringIO("""
package p1 "P1"
class p2 "P2"

p1 -m> p2
""")
        self.assertRaises(UMLError, parse, f)


    def test_package_import_error(self):
        """Test package import error
        """
        f = StringIO("""
package p1 "P1"
class p2 "P2"

p1 -i> p2
""")
        self.assertRaises(UMLError, parse, f)


    def test_usecase_include_extend(self):
        """Test use case inclusion and extension dependencies
        """
        f = StringIO("""
usecase u1 "U1"
usecase u2 "U2"

u1 -i> u2
u1 -e> u2
""")
        ast = parse(f)
        deps = [n for n in ast.unwind() if n.cls == 'dependency']
        self.assertEquals(['include'], deps[0].stereotypes)
        self.assertEquals(['extend'], deps[1].stereotypes)


    def test_usecase_include_error(self):
        """Test use case inclusion error
        """
        f = StringIO("""
usecase u1 "U1"
class u2 "U2"

u1 -i> u2
""")
        self.assertRaises(UMLError, parse, f)


    def test_usecase_extend_error(self):
        """Test use case extension error
        """
        f = StringIO("""
usecase u1 "U1"
class u2 "U2"

u1 -e> u2
""")
        self.assertRaises(UMLError, parse, f)


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
        ast = parse(f)
        dirs = [n.data['direction'] for n in ast.unwind() \
            if n.cls == 'association']
        self.assertEquals('c2', dirs[0].id)
        self.assertEquals('c2', dirs[1].id)
        self.assertFalse(dirs[2])


    def test_association_name(self):
        """Test association name
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
""")
        ast = parse(f)
        names = [n.name for n in ast.unwind() if n.cls == 'association']
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
        self.assertRaises(UMLError, parse, f)


    def test_association_head_only(self):
        """Test association with association end at head only
        """
        f = StringIO("""
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
    :: head [0..n]
""")
        ast = parse(f)
        assocs = [n for n in ast.unwind() if n.cls == 'association']
        self.assertEquals(['An association'], [n.name for n in assocs])
        assoc = assocs[0]
        self.assertEquals(0, len(assoc))
        self.assertEquals((None, None, None, 'unknown'), assoc.data['tail'])
        self.assertEquals((None, 'head', '0..n', 'unknown'), assoc.data['head'])


    def test_profile_extension(self):
        """Test profile extension
        """
        f = StringIO("""
stereotype s "S"
metaclass m "M"

s == m
""")
        ast = parse(f)
        exts = [n for n in ast.unwind() if n.cls == 'extension']
        self.assertEquals(1, len(exts))


# vim: sw=4:et:ai
