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
Line router tests.
"""

from cStringIO import StringIO
import unittest

from piuml.layout import Router
from piuml.data import Element, Pos, Size
from piuml.parser import parse, ParseError


class LineRouterTestCase(unittest.TestCase):
    """
    Line router tests.
    """
    def test_simple_pickup(self):
        """Test simple obstacles pickup
        """
        r = Router()

        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
class c4 "C4"
""")
        ast = parse(f)

        c1 = ast.cache['c1']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']
        c4 = ast.cache['c4']

        obstacles = r._pickup(ast, c1, c2)

        self.assertEquals([c3, c4], obstacles)


    def test_pickup_with_grouping(self):
        """Test obstacles pickup with grouping involved
        """
        r = Router()

        f = StringIO("""
class c1 "C1"
    class c11 "C11"
    class c12 "C12"
class c2 "C2"
    class c21 "C21"
    class c22 "C22"
class c3 "C3"
class c4 "C4"
""")
        ast = parse(f)

        c1 = ast.cache['c1']
        c11 = ast.cache['c11']
        c12 = ast.cache['c12']
        c2 = ast.cache['c2']
        c21 = ast.cache['c21']
        c22 = ast.cache['c22']
        c3 = ast.cache['c3']
        c4 = ast.cache['c4']

        obstacles = r._pickup(ast, c12, c21)

        self.assertEquals([c3, c4, c11, c22], obstacles)


    def test_obstacles_shapes(self):
        """Test extracting obstacles shapes
        """
        r = Router()
        e1 = Element('class')
        e1.style.pos = Pos(10, 10)
        e1.style.size = Size(4, 2)

        e2 = Element('class')
        e2.style.pos = Pos(20, 20)
        e2.style.size = Size(3, 1)

        e3 = Element('class')
        e3.style.pos = Pos(0, 0)
        e3.style.size = Size(6, 5)

        vo, ho = r._shapes((e1, e2, e3))
        self.assertEquals(6, len(vo))
        self.assertEquals(6, len(ho))

        self.assertEquals(e1, vo[0].node)
        self.assertEquals((Pos(10, 10), Pos(10, 12)), vo[0].line)
        self.assertEquals(e1, vo[1].node)
        self.assertEquals((Pos(14, 10), Pos(14, 12)), vo[1].line)

        self.assertEquals(e1, ho[0].node)
        self.assertEquals((Pos(10, 10), Pos(14, 10)), ho[0].line)
        self.assertEquals(e1, ho[1].node)
        self.assertEquals((Pos(10, 12), Pos(14, 12)), ho[1].line)


    def test_obstacles_sort(self):
        """Test sorting of obstacles
        """
        r = Router()
        e1 = Element('class', id='e1')
        e1.style.pos = Pos(10, 10)
        e1.style.size = Size(15, 2)

        e2 = Element('class', id='e2')
        e2.style.pos = Pos(20, 20)
        e2.style.size = Size(2, 1)

        e3 = Element('class', id='e3')
        e3.style.pos = Pos(0, 0)
        e3.style.size = Size(6, 5)

        vo, ho = r._shapes((e1, e2, e3))

        vs = r._sort(vo, vert=True)
        hs = r._sort(ho, vert=False)

        self.assertEquals([e3, e3, e1, e2, e2, e1], [o.node for o in vs])
        self.assertEquals([e3, e3, e1, e1, e2, e2], [o.node for o in hs])


# vim: sw=4:et:ai
