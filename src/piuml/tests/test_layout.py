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

from cStringIO import StringIO
import unittest

from piuml.layout import Layout
from piuml.parser import parse, ParseError

class AlignPostprocessTestCase(unittest.TestCase):
    def test_default_simple(self):
        """Test default, simple alignment
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c1', 'c2']], ast.align.middle)
        self.assertEquals([['c1', 'c2']], ast.align.hspan)


    def test_invalid_align(self):
        """Test invalid align specification
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"

    center: c1 c2
""")
        self.assertRaises(ParseError, parse, f)


    def test_defined_simple(self):
        """Test defined, simple alignment
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"

:layout:
    left: c2 c1 # note reorder
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c2', 'c1']], ast.align.left)
        self.assertEquals([['c2', 'c1']], ast.align.vspan)


    def test_orphaned(self):
        """Test orphaned (in alignment) elements
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"

:layout:
    left: c1 c3
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c1', 'c3']], ast.align.left)
        self.assertEquals([['c1', 'c3']], ast.align.vspan)

        # orphaned element alignment
        self.assertEquals([['c1', 'c2']], ast.align.hspan)
        self.assertEquals([['c1', 'c2']], ast.align.middle)


    def test_deep_align(self):
        """Test align with packaged elements
        """
        l = Layout()
        # diagram:
        # -- c --
        # |c1 c2| c4 c5
        # -------
        #     c3
        #
        f = StringIO("""
class c "C"
    class c1 "C1"
        class c2 "C2"
class c3 "C3"
class c4 "C4"
class c5 "C5"

:layout:
    left: c2 c3
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c', 'c4', 'c5']], ast.align.middle)
        self.assertEquals([['c', 'c4', 'c5']], ast.align.hspan)

        # c2 is replaced with c - lca
        self.assertEquals([['c', 'c3']], ast.align.vspan)
        self.assertEquals([['c2', 'c3']], ast.align.left)


    def test_default_interleave(self):
        """Test default align constraining with defined layout
        """
        l = Layout()
        # diagram:
        # a c d
        # b   e
        f = StringIO("""
class a "C1"
class b "C2"
class c "C3"
class d "C4"
class e "C5"

:layout:
    center: a b
    center: d e
""")
        ast = parse(f)
        l.create(ast)

        # default and defined alignment plays well
        self.assertEquals([['a', 'c', 'd']], ast.align.middle)
        self.assertEquals([['a', 'c', 'd']], ast.align.hspan)

        # check defined alignment
        self.assertEquals([['a', 'b'], ['d', 'e']], ast.align.vspan)
        self.assertEquals([['a', 'b'], ['d', 'e']], ast.align.center)


# vim: sw=4:et:ai
