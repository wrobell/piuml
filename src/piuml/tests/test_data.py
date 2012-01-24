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

import unittest

from piuml.data import Diagram, PackagingElement, Element, \
        MWalker, lca, lsb, preorder, unwind

"""
piUML language parser data model routines tests.
"""

class DataModelTestCase(unittest.TestCase):
    """
    piUML language parser data model simple tests.
    """
    def test_eq(self):
        """
        Test AST nodes equality
        """
        n1 = Element('b')
        n2 = Element('b')
        assert n1.id != n2.id

        self.assertNotEquals(n1, n2)

        self.assertEquals(n1, n1)
        self.assertEquals(n2, n2)


    def test_hash(self):
        """
        Test hashing of AST nodes
        """
        n1 = Element('b')
        n2 = Element('b')
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
        """
        Test LCA
        """
        n1 = Diagram()
        n1.id = 'n1'

        n2 = Element('a', id='n2')
        n3 = Element('a', id='n3')
        n1.children.extend((n2, n3))
        n2.parent = n1
        n3.parent = n1

        p = lca(n1, n2, n3)
        self.assertEquals('n1', p.id)


    def test_lsb(self):
        """
        Test LSB
        """
        n1 = Diagram()
        n1.id = 'n1'

        n2 = PackagingElement('a', id='n2')
        n3 = PackagingElement('a', id='n3')
        n4 = PackagingElement('a', id='n4')

        n1.children.extend((n2, n3))
        n2.children.append(n4)

        n2.parent = n1
        n3.parent = n1
        n4.parent = n2

        siblings = lsb(n1, n3, n4)
        self.assertEquals([n3, n2], siblings)


    def test_preorder(self):
        """
        Test preorder traversing
        """
        def f(n):
            f.t += 1
        f.t = 0

        n1 = Diagram()
        n1.id = 'n1'

        n2 = PackagingElement('a', id='n2')
        n3 = PackagingElement('a', id='n3')
        n4 = Element('a', id='n4')

        n1.children.extend((n2, n3))
        n2.children.append(n4)

        preorder(n1, f)
        self.assertEquals(4, f.t)


    def test_mwalker(self):
        """
        Test method walker
        """
        class MW(MWalker):
            def __init__(self):
                self.walked = []

            def visit(self, n):
                self.walked.append(n)

            v_diagram = v_packagingelement = v_element = visit


        mw = MW()

        n1 = Diagram()
        n1.id = 'n1'

        n2 = PackagingElement('a', id='n2')
        n3 = PackagingElement('a', id='n3')
        n4 = Element('a', id='n4')

        n1.children.extend((n2, n3))
        n2.children.append(n4)

        mw.preorder(n1)
        self.assertEquals([n1, n2, n4, n3], mw.walked)


    def test_unwind(self):
        """
        Test unwind
        """
        n1 = Diagram()
        n1.id = 'n1'

        n2 = PackagingElement('a', id='n2')
        n3 = PackagingElement('a', id='n3')
        n4 = Element('a', id='n4')

        n1.children.extend((n2, n3))
        n2.children.append(n4)

        n2.parent = n1
        n3.parent = n1
        n4.parent = n2

        self.assertEquals([n1, n2, n4, n3], list(unwind(n1)))


# vim: sw=4:et:ai
