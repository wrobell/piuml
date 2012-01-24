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
Tests of constraint solver and constraints.
"""

import unittest

from piuml.layout.solver import Solver, TopEq, BottomEq, MinSize, MinHDist
from piuml.style import BoxStyle, Size

class SolverTestCase(unittest.TestCase):
    """
    Constraint solver test case.
    """
    def test_solver(self):
        """Test (simply) constraint solver
        """
        r1 = BoxStyle()
        r2 = BoxStyle()
        r3 = BoxStyle()
        
        r1.min_size = Size(10, 10)
        r2.min_size = Size(20, 5)
        r3.min_size = Size(5, 15)

        s = Solver()
        s.add(MinSize(r1))
        s.add(MinSize(r2))
        s.add(MinSize(r3))
        s.add(TopEq(r1, r2))
        s.add(MinHDist(r2, r3, 10))

        s.solve()

        self.assertTrue(r1.size.width >= 10)
        self.assertTrue(r1.size.height >= 10)

        self.assertTrue(r2.size.width >= 20)
        self.assertTrue(r2.size.height >= 5)

        self.assertTrue(r3.size.width >= 5)
        self.assertTrue(r3.size.height >= 15)

        self.assertEquals(40, r1.size.height)
        self.assertEquals(40, r2.size.height)

        self.assertTrue(r3.pos.x - r2.pos.x - r2.size.width >= 10)


    def test_bottom_eq(self):
        """Test bottom eq constraint
        """
        r1 = BoxStyle()
        r2 = BoxStyle()
        
        r1.min_size = Size(10, 10)
        r2.min_size = Size(20, 5)
        r1.size = Size(10, 10)
        r2.size = Size(20, 5)

        s = Solver()
        s.add(MinSize(r1))
        s.add(MinSize(r2))
        s.add(BottomEq(r1, r2))

        s.solve()

        self.assertTrue(r1.size.width >= 10)
        self.assertTrue(r1.size.height >= 10)

        self.assertTrue(r2.size.width >= 20)
        self.assertTrue(r2.size.height >= 5)

        self.assertEquals(0, r1.pos.y)
        self.assertEquals(5, r2.pos.y)


# vim: sw=4:et:ai
