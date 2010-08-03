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

import unittest

from piuml.data import Diagram, Dummy, lca, lsb

"""
piUML language parser data model routines tests.
"""

class DataModelTestCase(unittest.TestCase):
    """
    piUML language parser data model simple tests.
    """
    def test_eq(self):
        """
        Test AST nodes equality.
        """
        n1 = Dummy('b')
        n2 = Dummy('b')
        assert n1.id != n2.id

        self.assertNotEquals(n1, n2)

        self.assertEquals(n1, n1)
        self.assertEquals(n2, n2)


    def test_hash(self):
        """
        Test hashing of AST nodes.
        """
        n1 = Dummy('b')
        n2 = Dummy('b')
        assert n1.id != n2.id

        s = set([n1, n2])
        self.assertEquals(2, len(s))
        self.assertTrue(n1 in s)
        self.assertTrue(n2 in s)

       

class TreeTestCase(unittest.TestCase):
    """
    Tree (AST tree) algorithms tests.
    """
    def test_lca(self):
        """Test LCA
        """
        n1 = Diagram()
        n1.id = 'n1'
        n1.cache['n1'] = n1

        n2 = Dummy('a', id='n2')
        n3 = Dummy('a', id='n3')
        n1.reorder()
        n1.extend((n2, n3))
        n2.parent = n1
        n3.parent = n1

        p = lca(n1, n2, n3)
        self.assertEquals('n1', p.id)


    def test_lsb(self):
        """Test LSB
        """
        n1 = Diagram()
        n1.id = 'n1'

        n2 = Dummy('a', id='n2')
        n3 = Dummy('a', id='n3')
        n4 = Dummy('a', id='n4')

        n1.extend((n2, n3))
        n2.append(n4)

        n2.parent = n1
        n3.parent = n1
        n4.parent = n2

        siblings = lsb(n1, [n3, n4])
        self.assertEquals([n3, n2], siblings)


# vim: sw=4:et:ai
