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

from piuml.layout import PreLayout
from piuml.parser import parse

class AlignPostprocessTestCase(unittest.TestCase):
    def test_default_simple(self):
        """Test default, simple alignment
        """
        l = PreLayout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c1', 'c2']], ast.align.middle)
        self.assertEquals([['c1', 'c2']], ast.align.hspan)


    def test_defined_simple(self):
        """Test defined, simple alignment
        """
        l = PreLayout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"

align=left: c2 c1 # note reorder
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c2', 'c1']], ast.align.left)
        self.assertEquals([['c2', 'c1']], ast.align.vspan)


    def test_deep_align(self):
        """Test align with packaged elements
        """
        l = PreLayout()
        f = StringIO("""
class c "C"
    class c1 "C1"
        class c2 "C2"
class c3 "C3"
class c4 "C4"
class c5 "C5"

align=left: c2 c3
""")
        ast = parse(f)
        l.create(ast)
        self.assertEquals([['c4', 'c5']], ast.align.middle)
        self.assertEquals([['c2', 'c3']], ast.align.left)

        # c2 is replaced with c - lca
        self.assertEquals([['c4', 'c5']], ast.align.hspan)
        self.assertEquals([['c', 'c3']], ast.align.vspan)

        #self.assertEquals([['c', 'c3']], ast.align.vspan)


# vim: sw=4:et:ai
