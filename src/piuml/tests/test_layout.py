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

from piuml.layout.cl import ConstraintLayout, MinHDist, MinVDist, \
    MiddleEq, CenterEq, LeftEq, RightEq, TopEq, BottomEq
from piuml.parser import parse, ParseError

import unittest


class LayoutTestCase(unittest.TestCase):
    """
    Layout tests.
    """
    def _process(self, f):
        """
        Process layout and return the root node.
        """
        l = self._layout = ConstraintLayout()
        n = parse(f)
        l._prepare(n)
        l.preorder(n, reverse=True)
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
        c1 = n[0].style
        c2 = n[1].style
        c3 = n[2].style
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
        c1 = n[0].style
        c2 = n[1].style

        self._check_c(LeftEq, c2, c1)
        self._check_c(MinVDist, c2, c1)
        self._check_c(None, c1, c2) # note reorder above


    def test_orphaned(self):
        """
        Test orphaned (due to alignment) elements
        """
        n = self._process("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
class c4 "C4"

:layout:
    right: c1 c3
""")
        c1 = n[0].style
        c2 = n[1].style
        c3 = n[2].style
        c4 = n[3].style

        self._check_c(RightEq, c1, c3)
        self._check_c(MinVDist, c1, c3)

        # default alignment
        self._check_c(MiddleEq, c2, c4)
        self._check_c(MinHDist, c2, c4)

        self._check_c(None, c1, c2)
        self._check_c(None, c1, c4)
        self._check_c(None, c3, c2)
        self._check_c(None, c3, c4)


    def test_independent(self):
        self.fail('to be implemented')


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
    center: c2 c3
""")
        c = n[0].style
        c2 = n[0][1].style
        c3 = n[1].style
        c4 = n[2].style
        c5 = n[3].style

        self._check_c(CenterEq, c2, c3)
        self._check_c(MinVDist, c, c3)
        self._check_c_not(MinVDist, c2, c3)

        self._check_c(MiddleEq, c, c4)
        self._check_c(MiddleEq, c4, c5)
        self._check_c(MinHDist, c, c4)
        self._check_c(MinHDist, c4, c5)


    def test_default_interleave(self):
        """
        Test default align constraining with defined layout
        """
        l = Layout()
        # diagram:
        # a c d
        # b   e
        f = """
class a "C1"
class b "C2"
class c "C3"
class d "C4"
class e "C5"

:layout:
    left: a b
    right: d e
"""
        n = parse(f)
        a = n[0]
        b = n[1]
        c = n[2]
        d = n[3]
        e = n[4]

        l._prepare(n)
        align = n.data['align']
        self.assertEquals(2, len(align))
        self.assertEquals('left', align[0].cls)
        self.assertEquals([a, b], align[0].align)
        self.assertEquals([a, b], align[0].span)
        self.assertEquals('right', align[1].cls)
        self.assertEquals([d, e], align[1].align)
        self.assertEquals([d, e], align[1].span)

        span, default = l._span_matrix(n, align)

        self.assertEquals('middle', default.cls)
        self.assertEquals([a, c, d], default.align)
        self.assertEquals([a, c, d], default.span)

        self.assertEquals([
            [a, b],
            [None, None],
            [c, None],
            [d, e],
            [None, None],
        ], span.data)


    def test_deep_default_interleave(self):
        """
        Test deep default align constraining with defined layout
        """
        l = Layout()
        # diagram:
        # -- c --
        # |c1 c2|
        # -------
        #  c3 c4
        #
        f = """
class c "C"
    class c1 "C1"
    class c2 "C2"
class c3 "C3"
class c4 "C4"

:layout:
    right: c1 c3
    left: c2 c4
"""
        n = parse(f)
        c = n[0]
        c1 = n[0][0]
        c2 = n[0][1]
        c3 = n[1]
        c4 = n[2]

        l._prepare(n)
        align = n.data['align']
        self.assertEquals(2, len(align))
        self.assertEquals('right', align[0].cls)
        self.assertEquals([c1, c3], align[0].align)
        self.assertEquals([c, c3], align[0].span)
        self.assertEquals('left', align[1].cls)
        self.assertEquals([c2, c4], align[1].align)
        self.assertEquals([c, c4], align[1].span)

        span, default = l._span_matrix(n, align)

        self.assertTrue(default is None)

        self.assertEquals([
            [c, c3, c4],
            [None, None, None],
            [None, None, None],
        ], span.data)


    def test_star_layout(self):
        """
        Test star layout
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
    middle: a b c
    center: d b e
""")
        a = n[0].style
        b = n[1].style
        c = n[2].style
        d = n[3].style
        e = n[4].style

        self._check_c(MinHDist, a, b)
        self._check_c(MiddleEq, a, b)
        self._check_c(MinHDist, b, c)
        self._check_c(MiddleEq, b, c)
        self._check_c(None, a, c)
        self._check_c(None, b, b)
        self._check_c(MinVDist, d, b)
        self._check_c(CenterEq, d, b)
        self._check_c(MinVDist, b, e)
        self._check_c(CenterEq, b, e)


# vim: sw=4:et:ai
