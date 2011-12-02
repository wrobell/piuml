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
Test Cairo based renderer text and box (including compartments) size
calculation.
"""

from piuml.renderer.cr import _head_size
from piuml.data import BoxStyle, Size, Area

import unittest

class NameTestCase(unittest.TestCase):
    """
    Test element's name size calculations.
    """
    def test_head_size(self):
        """
        Test head size
        """
        style = BoxStyle()
        style.size = Size(80, 25)
        style.compartment[0] = 10
        self.assertEquals(25, _head_size(style))


    def test_head_size_with_one_cmp(self):
        """
        Test head size with one additional compartment
        """
        style = BoxStyle()
        style.size = Size(80, 55)
        style.compartment[0] = 10
        style.compartment.append(15)
        self.assertEquals(30, _head_size(style)) # 55 - 5 * 2 (pad) - 15


    def test_head_size_with_two_cmp(self):
        """
        Test head size with two additional compartments
        """
        style = BoxStyle()
        style.size = Size(80, 100)
        style.compartment[0] = 10
        style.compartment.append(15)
        style.compartment.append(10)
        self.assertEquals(55, _head_size(style)) # 100 - 5 * 4 (pad) - 25


# vim: sw=4:et:ai
