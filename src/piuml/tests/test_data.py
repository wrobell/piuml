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

from piuml.data import Diagram, Dummy, SpanMatrix, lca, lsb

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


class SpanMatrixTestCase(unittest.TestCase):
    """
    Span matrix tests.
    """
    def test_empty(self):
        """Test empty span matrix
        """
        m = SpanMatrix()
        self.assertEquals(0, len(m.data))


    def test_empty_insert_row(self):
        """Test inserting row into empty matrix
        """
        m = SpanMatrix()
        m.insert_row(0)
        self.assertEquals(1, len(m.data))
        self.assertEquals(1, len(m.data[0]))
        self.assertEquals(None, m[0, 0])


    def test_insert_row(self):
        """Test inserting row
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        m.insert_row(1)
        d = [t[1] for t in m.data] # get row
        self.assertEquals([None, None], d)


    def test_empty_insert_col(self):
        """Test inserting col into empty matrix
        """
        m = SpanMatrix()
        m.insert_col(0)
        self.assertEquals(1, len(m.data))
        self.assertEquals(1, len(m.data[0]))
        self.assertEquals(None, m[0, 0])


    def test_insert_col(self):
        """Test inserting column
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        m.insert_col(1)
        self.assertEquals([None] * 4, m.data[1])


    def test_get(self):
        """Test getting an item
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        self.assertEquals('B', m[0, 1])
        self.assertEquals(3, m[1, 2])


    def test_set(self):
        """Test setting an item
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        assert 3 == m.data[1][2]
        m[1, 2] = 'X'
        self.assertEquals('X', m.data[1][2])


    def test_hspan(self):
        """Test horizontal span
        """
        m = SpanMatrix()
        m.hspan('A', 'B')
        self.assertEquals([['A'], ['B']], m.data)
        m.hspan('A', 'C')
        self.assertEquals([['A'], ['C'], ['B']], m.data)
        m.hspan('B', 'D')
        self.assertEquals([['A'], ['C'], ['B'], ['D']], m.data)
        m.hspan('F', 'A')
        self.assertEquals([['F'], ['A'], ['C'], ['B'], ['D']], m.data)


    def test_vspan(self):
        """Test vertical span
        """
        m = SpanMatrix()
        m.vspan('A', 'B')
        self.assertEquals([['A','B']], m.data)
        m.vspan('A', 'C')
        self.assertEquals([['A','C','B']], m.data)
        m.vspan('B', 'D')
        self.assertEquals([['A','C','B','D']], m.data)
        m.vspan('F', 'A')
        self.assertEquals([['F','A','C','B','D']], m.data)


# vim: sw=4:et:ai
