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


class ParserTestCase(unittest.TestCase):
    """
    Basic parser tests.
    """
    def test_string(self):
        """
        Test string parsing.
        """
        f = "class a 'A1'"
        n = parse(f)
        self.assertEquals('A1', n.children[0].name)

        f = 'class a "A2"'
        n = parse(f)
        self.assertEquals('A2', n.children[0].name)


class PackagingTestCase(unittest.TestCase):
    """
    Element packaging test case.
    """
    def test_empty(self):
        """
        Test packaging elements without children
        """
        # note empty line after class definition
        f = """
class a <<aaa>> 'A'

"""
        n = parse(f)
        cls = [k for k in unwind(n) if k.cls == 'class']
        self.assertEquals(1, len(cls))


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
    def test_element_st_parsing(self):
        """
        Test element stereotype parsing
        """
        f = 'interface a <<test>> "A"'
        n = parse(f)
        self.assertEquals(['interface', 'test'], n[0].stereotypes)

        f = 'interface a <<t1, t2>> "A"'
        n = parse(f)
        self.assertEquals(['interface', 't1', 't2'], n[0].stereotypes)


    def test_pelement_st_parsing(self):
        """
        Test packaging element stereotype parsing
        """
        f = 'component a <<test>> "A"'
        n = parse(f)
        self.assertEquals(['component', 'test'], n[0].stereotypes)

        f = 'component a <<t1, t2>> "A"'
        n = parse(f)
        self.assertEquals(['component', 't1', 't2'], n[0].stereotypes)


    def test_dependency_stereotypes(self):
        """
        Test dependency stereotype parsing
        """
        f = """
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a -> <<test>> b
"""
        n = parse(f)
        self.assertEquals(['test'], n[2].stereotypes)



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



class DependencyTestCase(unittest.TestCase):
    """
    Dependency tests.
    """
    def test_dependency(self):
        """
        Test dependency creation
        """
        f = """
package p1 "P1"
package p2 "P2"

p1 -> p2
p1 <- p2
"""
        n = parse(f)
        self.assertEquals('dependency', n[2].cls)
        self.assertEquals('dependency', n[3].cls)


    def test_package_merge_import(self):
        """
        Test package merge and package import
        """
        f = """
package p1 "P1"
package p2 "P2"

p1 -m> p2
p1 -i> p2
"""
        n = parse(f)
        self.assertEquals(['merge'], n[2].stereotypes)
        self.assertEquals(['import'], n[3].stereotypes)


    def test_package_merge_error(self):
        """
        Test package merge error
        """
        f = """
package p1 "P1"
class p2 "P2"

p1 -m> p2
"""
        self.assertRaises(UMLError, parse, f)


    def test_package_import_error(self):
        """
        Test package import error
        """
        f = """
package p1 "P1"
class p2 "P2"

p1 -i> p2
"""
        self.assertRaises(UMLError, parse, f)


    def test_usecase_include_extend(self):
        """
        Test use case inclusion and extension dependencies
        """
        f = """
usecase u1 "U1"
usecase u2 "U2"

u1 -i> u2
u1 -e> u2
"""
        n = parse(f)
        self.assertEquals(['include'], n[2].stereotypes)
        self.assertEquals(['extend'], n[3].stereotypes)


    def test_usecase_include_error(self):
        """
        Test use case inclusion error
        """
        f = """
usecase u1 "U1"
class u2 "U2"

u1 -i> u2
"""
        self.assertRaises(UMLError, parse, f)


    def test_usecase_extend_error(self):
        """
        Test use case extension error
        """
        f = """
usecase u1 "U1"
class u2 "U2"

u1 -e> u2
"""
        self.assertRaises(UMLError, parse, f)


class AssociationTestCase(unittest.TestCase):
    """
    Association tests.
    """
    def test_association(self):
        """
        Test association creation
        """
        f = """
package p1 "P1"
package p2 "P2"

p1 == p2
"""
        n = parse(f)
        self.assertEquals('association', n[2].cls)


    def test_association_dir(self):
        """
        Test association direction
        """
        f = """
class c1 "C1"
class c2 "C2"
class c3 "C3"

c1 =>= c2
c2 =<= c3
c3 == c1
"""
        n = parse(f)
        self.assertEquals('c2', n[3].data['direction'].id)
        self.assertEquals('c2', n[4].data['direction'].id)
        self.assertTrue(n[5].data['direction'] is None)


    def test_association_name(self):
        """
        Test association name
        """
        f = """
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
"""
        n = parse(f)
        self.assertEquals('An association', n[2].name)


    def test_association_stereotypes(self):
        """
        Test association stereotype parsing
        """
        f = """
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a == <<t1, t2>> b
a == <<t1, t2, t3>> 'a name' b
"""
        n = parse(f)
        self.assertEquals(['t1', 't2'], n[2].stereotypes)
        self.assertEquals('a name', n[3].name)
        self.assertEquals(['t1', 't2', 't3'], n[3].stereotypes)


    def test_association_navigability(self):
        """
        Test association navigability parsing
        """
        f = """
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a == b
a ==> b
a <== b
a <==> b
a ==x b
a x== b
a x==x b
"""
        n = parse(f)
        self.assertEquals('unknown', n[2].data['tail'][2])
        self.assertEquals('unknown', n[2].data['head'][2])
        self.assertEquals('unknown', n[3].data['tail'][2])
        self.assertEquals('navigable', n[3].data['head'][2])
        self.assertEquals('navigable', n[4].data['tail'][2])
        self.assertEquals('unknown', n[4].data['head'][2])
        self.assertEquals('navigable', n[5].data['tail'][2])
        self.assertEquals('navigable', n[5].data['head'][2])
        self.assertEquals('unknown', n[6].data['tail'][2])
        self.assertEquals('none', n[6].data['head'][2])
        self.assertEquals('none', n[7].data['tail'][2])
        self.assertEquals('unknown', n[7].data['head'][2])
        self.assertEquals('none', n[8].data['tail'][2])
        self.assertEquals('none', n[8].data['head'][2])


    def test_association_aggregation(self):
        """
        Test association aggregation parsing
        """
        f = """
class a <<aaa>> 'A'
class b <<bbb>> 'B'

a ==O b
a O== b
a O==O b
a ==* b
a *== b
a *==* b
"""
        n = parse(f)
        self.assertEquals('unknown', n[2].data['tail'][2])
        self.assertEquals('shared', n[2].data['head'][2])
        self.assertEquals('shared', n[3].data['tail'][2])
        self.assertEquals('unknown', n[3].data['head'][2])
        self.assertEquals('shared', n[4].data['tail'][2])
        self.assertEquals('shared', n[4].data['head'][2])
        self.assertEquals('unknown', n[5].data['tail'][2])
        self.assertEquals('composite', n[5].data['head'][2])
        self.assertEquals('composite', n[6].data['tail'][2])
        self.assertEquals('unknown', n[6].data['head'][2])
        self.assertEquals('composite', n[7].data['tail'][2])
        self.assertEquals('composite', n[7].data['head'][2])


    def test_association_ends(self):
        """
        Test association ends
        """
        f = """
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
    : tail-attr [1..n]
    : head-attr [0..n]
"""
        n = parse(f)
        data = n[2].data
        self.assertEquals('tail-attr', data['tail'][1].name)
        self.assertEquals('head-attr', data['head'][1].name)
        self.assertEquals('[1..n]', str(data['tail'][1].mult))
        self.assertEquals('[0..n]', str(data['head'][1].mult))


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


    def test_association_ends_error(self):
        """
        Test association with too many ends
        """
        f = """
class c1 "C1"
class c2 "C2"

c1 =>= c2
    : a
    : b
    : c
"""
        self.assertRaises(UMLError, parse, f)


    def test_profile_extension(self):
        """
        Test profile extension
        """
        f = """
stereotype s "S"
metaclass m "M"

s == m
"""
        n = parse(f)
        self.assertEquals('extension', n[2].cls)


# vim: sw=4:et:ai
