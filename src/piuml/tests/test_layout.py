#
# piUML - UML diagram generator.
#
# Copyright (C) 2010 - 2012 by Artur Wroblewski <wrobell@pld-linux.org>
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
Layout (alignment, span matrix, etc) tests.
"""

from piuml.layout.cl import Layout, MinHDist, MinVDist, \
    MiddleEq, CenterEq, LeftEq, RightEq, TopEq, BottomEq
from piuml.parser import parse, ParseError
from piuml.data import unwind

import unittest

def find_node(ast, id):
    for n in unwind(ast):
        if hasattr(n, 'id') and n.id == id:
            return n
    raise ValueError('Cannot find node {}'.format(id))

def find_style(ast, id):
    return find_node(ast, id).style


class LayoutTestCase(unittest.TestCase):
    """
    Layout tests.
    """
    def _process(self, f):
        """
        Process layout and return the root node.
        """
        n = parse(f)
        l = self._layout = Layout(n)
        l.layout(solve=False)
        return n


    def _check_c(self, constraint, *variables):
        """
        Check if constraint is set between variables.

        If constraint is None, then check if there are no constraints
        between variables.
        """
        c = {c.__class__ for c in self._layout.solver.get(*variables)}
        if constraint:
            self.assertTrue(constraint in c)
        else:
            self.assertFalse(c)


    def _check_c_not(self, constraint, *variables):
        """
        Check if constraint is _not_ set between variables.
        """
        c = {c.__class__ for c in self._layout.solver.get(*variables)}
        self.assertFalse(constraint in c)


    def test_default_simple(self):
        """
        Test default, simple alignment
        """
        n = self._process("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
""")
        c1n = find_node(n, 'c1')
        c2n = find_node(n, 'c2')
        c3n = find_node(n, 'c3')

        c1 = c1n.style
        c2 = c2n.style
        c3 = c3n.style

        # no artificial groups
        self.assertEquals([c1n, c2n, c3n], n.children)

        self.assertTrue(n.data.get('align') is None)
        self._check_c(MiddleEq, c1, c2)
        self._check_c(MinHDist, c1, c2)
        self._check_c(MiddleEq, c2, c3)
        self._check_c(MinHDist, c2, c3)


    def test_defined_simple(self):
        """
        Test defined, simple alignment
        """

        n = self._process("""
class c1 "C1"
class c2 "C2"

# note reorder below
:layout:
    left: c2 c1
""")
        c1 = find_style(n, 'c1')
        c2 = find_style(n, 'c2')

        self._check_c(LeftEq, c2, c1)
        self._check_c(MinVDist, c2, c1)
        self._check_c(None, c1, c2) # note reorder above


    def test_all_used(self):
        """
        Test layout with all nodes used for alignment
        """
        # diagram:
        # 
        # c1
        # c3
        # c2
        n = self._process("""
class c1 "C1"
class c2 "C2"
class c3 "C3"

:layout:
    right g1: c1 c3
    left g2: c3 c2
""")
        c1 = find_style(n, 'c1')
        c2 = find_style(n, 'c2')
        c3 = find_style(n, 'c3')

        self._check_c_not(MiddleEq, c1, c3)
        self._check_c_not(MinHDist, c1, c3)


    def test_orphaned(self):
        """
        Test orphaned (due to alignment) elements
        """
        # diagram:
        # 
        # c1 c4 
        # c3
        # c2
        n = self._process("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
class c4 "C4"

:layout:
    right g1: c1 c3 c2
""")
        c1 = find_style(n, 'c1')
        c2 = find_style(n, 'c2')
        c3 = find_style(n, 'c3')
        c4 = find_style(n, 'c4')

        g1 = find_style(n, 'g1')

        self._check_c(MiddleEq, c1, c4)
        self._check_c(MinHDist, g1, c4)

        self._check_c(RightEq, c1, c3)
        self._check_c(MinVDist, c1, c3)
        self._check_c(RightEq, c3, c2)
        self._check_c(MinVDist, c3, c2)

        self._check_c(None, c1, c2)
        self._check_c(None, c2, c3) # note the order of c1, c3, c2
        self._check_c(None, c3, c4)


    def test_deep_align(self):
        """
        Test align with packaged elements
        """
        # diagram:
        # -- c --
        # |c1 c2| c4 c5
        # -------
        #     c3
        #
        n = self._process("""
class c "C"
    class c1 "C1"
    class c2 "C2"
class c3 "C3"
class c4 "C4"
class c5 "C5"

:layout:
    center g1: c2 c3
""")
        cn = find_node(n, 'c')
        c1n = find_node(n, 'c1')
        c2n = find_node(n, 'c2')
        c3n = find_node(n, 'c3')
        c4n = find_node(n, 'c4')
        c5n = find_node(n, 'c5')
        g1n = find_node(n, 'g1')
        g0n = g1n.parent

        c = cn.style
        c1 = c1n.style
        c2 = c2n.style
        c3 = c3n.style
        c4 = c4n.style
        c5 = c5n.style
        g0 = g0n.style
        g1 = g1n.style

        self.assertEquals([g1n, c4n, c5n], g0n.children)
        self.assertEquals([cn, c3n], g1n.children)

        self._check_c(CenterEq, c2, c3)
        self._check_c(MinVDist, c, c3)
        self._check_c_not(MinVDist, c2, c3)

        self._check_c(MiddleEq, c, c4)
        self._check_c(MiddleEq, c4, c5)
        self._check_c(MinHDist, g1, c4)
        self._check_c(MinHDist, c4, c5)


    def test_deep_auto_default_up_layer(self):
        """
        Test align with packaged elements and upper layer defaulting
        """
        # diagram:
        # --- g1 ---
        # |-- c1 --|
        # ||c3  c4||
        # |--------|
        # |-- c2 --|
        # ||c5  c6||
        # |--------|
        # ----------
        n = self._process("""
class c1 "C1"
    class c3 "C3"
    class c4 "C4"
class c2 "C2"
    class c5 "C5"
    class c6 "C6"

# check if c1 and c2 alignment default is ok!
:layout:
    center g1: c3 c5
""")
        c1n = find_node(n, 'c1')
        c2n = find_node(n, 'c2')
        c3n = find_node(n, 'c3')
        c5n = find_node(n, 'c5')
        g1n = find_node(n, 'g1')

        c1 = c1n.style
        c2 = c2n.style
        c3 = c3n.style
        c5 = c5n.style
        g1 = g1n.style

        self.assertEquals([c1n, c2n], g1n.children)

        # check the below just in case
        self._check_c(CenterEq, c3, c5)
        self._check_c_not(MinVDist, c3, c5)

        # the most important checks in this test
        # check for both constraints!
        self._check_c_not(MinHDist, c1, c2)
        self._check_c(MinVDist, c1, c2)


    def test_default_interleave(self):
        """
        Test default align constraining with defined layout
        """
        # diagram:
        # a c d
        # b   e
        n = self._process("""
class a "C1"
class b "C2"
class c "C3"
class d "C4"
class e "C5"

:layout:
    left g1: a b
    right g2: d e
""")
        a = find_style(n, 'a')
        b = find_style(n, 'b')
        c = find_style(n, 'c')
        d = find_style(n, 'd')
        e = find_style(n, 'e')
        g1 = find_style(n, 'g1')
        g2 = find_style(n, 'g2')

        self._check_c(MiddleEq, a, c)
        self._check_c(MinHDist, g1, c)
        self._check_c(MiddleEq, c, d)
        self._check_c(MinHDist, c, g2)

        self._check_c(LeftEq, a, b)
        self._check_c(MinVDist, a, b)
        self._check_c(RightEq, d, e)
        self._check_c(MinVDist, d, e)


    def test_default_interleave_all(self):
        """
        Test default align constraining with defined layout and all used
        """
        # diagram:
        # a c
        # b d
        #   e
        n = self._process("""
class a "C1"
class b "C2"
class c "C3"
class d "C4"
class e "C5"

:layout:
    left g1: a b
    right g2: c d e
""")
        a = find_style(n, 'a')
        b = find_style(n, 'b')
        c = find_style(n, 'c')
        d = find_style(n, 'd')
        e = find_style(n, 'e')

        g1 = find_style(n, 'g1')
        g2 = find_style(n, 'g2')

        self._check_c(MiddleEq, a, c)
        self._check_c(MinHDist, g1, g2)

        self._check_c(LeftEq, a, b)
        self._check_c(MinVDist, a, b)
        self._check_c(RightEq, c, d)
        self._check_c(MinVDist, c, d)
        self._check_c(RightEq, d, e)
        self._check_c(MinVDist, d, e)


    def test_deep_default_interleave(self):
        """
        Test deep default align constraining with defined layout
        """
        # diagram:
        # -- c --
        # |c1 c2|
        # -------
        #  c3 c4
        #
        n = self._process("""
class c "C"
    class c1 "C1"
    class c2 "C2"
class c3 "C3"
class c4 "C4"

:layout:
    right g1: c1 c3
    left g2: c2 c4
""")
        c = find_style(n, 'c')
        c1 = find_style(n, 'c1')
        c2 = find_style(n, 'c2')
        c3 = find_style(n, 'c3')
        c4 = find_style(n, 'c4')
        g1 = find_style(n, 'g1')

        self._check_c(RightEq, c1, c3)
        self._check_c(MinVDist, c, c3)
        self._check_c(LeftEq, c2, c4)
        self._check_c(MinVDist, g1, c4)

        self._check_c(MiddleEq, c1, c2)
        self._check_c(MinHDist, c1, c2)


    def test_cross_layout(self):
        """
        Test cross layout
        """
        # diagram:
        #   d
        # a b c
        #   e  
        n = self._process("""
class a "C1"
class b "C2"
class c "C3"
class d "C4"
class e "C5"

:layout:
    middle g1: a b c
    center g2: d b e
""")
        g1 = find_style(n, 'g1')
        g2 = find_style(n, 'g2')
        a = find_style(n, 'a')
        b = find_style(n, 'b')
        c = find_style(n, 'c')
        d = find_style(n, 'd')
        e = find_style(n, 'e')

        self._check_c(None, a, d)
        self._check_c(None, a, c)
        self._check_c(None, b, b)

        self._check_c(MinHDist, a, b)
        self._check_c(MiddleEq, a, b)
        self._check_c(MinHDist, b, c)
        self._check_c(MiddleEq, b, c)
        self._check_c(MinVDist, d, g1)
        self._check_c(CenterEq, d, b)
        self._check_c(MinVDist, g1, e)
        self._check_c(CenterEq, b, e)


# vim: sw=4:et:ai
