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
Layout (alignment, span matrix, etc) tests.
"""

from io import StringIO
import unittest

from piuml.layout.cl import Layout, SpanMatrix
from piuml.parser import parse, ParseError


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
        """Test inserting row into empty span matrix
        """
        m = SpanMatrix()
        m.insert_row(0)
        self.assertEquals(1, len(m.data))
        self.assertEquals(1, len(m.data[0]))
        self.assertEquals(None, m[0, 0])


    def test_insert_row(self):
        """Test inserting row into span matrix
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        m.insert_row(1)
        d = [t[1] for t in m.data] # get row
        self.assertEquals([None, None], d)


    def test_empty_insert_col(self):
        """Test inserting col into empty span matrix
        """
        m = SpanMatrix()
        m.insert_col(0)
        self.assertEquals(1, len(m.data))
        self.assertEquals(1, len(m.data[0]))
        self.assertEquals(None, m[0, 0])


    def test_insert_col(self):
        """Test inserting column into span matrix
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        m.insert_col(1)
        self.assertEquals([None] * 4, m.data[1])


    def test_get(self):
        """Test getting an item from span matrix
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        self.assertEquals('B', m[0, 1])
        self.assertEquals(3, m[1, 2])


    def test_set(self):
        """Test setting an item in span matrix
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        assert 3 == m.data[1][2]
        m[1, 2] = 'X'
        self.assertEquals('X', m.data[1][2])


    def test_getting_rows(self):
        """Test getting span matrix rows
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        self.assertEquals([['A', 1], ['B', 2], ['C', 3], ['D', 4]], m.rows())


    def test_getting_columns(self):
        """Test getting span matrix columns
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D'], [1, 2, 3, 4]]
        self.assertEquals([['A', 'B', 'C', 'D'], [1, 2, 3, 4]], m.columns())


    def test_hspan(self):
        """Test horizontal span
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D', 'E']] # create vertical column

        m.hspan('A', 'B')
        self.assertEquals([
            ['A', None, 'C', 'D', 'E'],
            ['B', None, None, None, None],
        ], m.data)

        m.hspan('A', 'C')
        self.assertEquals([
            ['A', None, None, 'D', 'E'],
            ['B', None, None, None, None],
            ['C', None, None, None, None],
        ], m.data)

        m.hspan('B', 'D')
        self.assertEquals([
            ['A', None, None, None, 'E'],
            ['B', None, None, None, None],
            ['C', None, None, None, None],
            ['D', None, None, None, None],
        ], m.data)

        m.hspan('E', 'A')
        self.assertEquals([
            [None, None, None, None, 'E'],
            ['B', None, None, None, 'A'],
            ['C', None, None, None, None],
            ['D', None, None, None, None],
        ], m.data)


    def test_hspan_independent(self):
        """Test horizontal span with independent requests
        """
        m = SpanMatrix()
        m.data = [['A', 'B', 'C', 'D', 'E']] # create vertical column

        m.hspan('A', 'B')
        m.hspan('C', 'D')
        self.assertEquals([
            ['A', None, 'C', None, 'E'],
            ['B', None, 'D', None, None],
        ], m.data)


    def test_vspan(self):
        """Test vertical span
        """
        m = SpanMatrix('A', 'B', 'C', 'D', 'E')

        m.vspan('A', 'B')
        self.assertEquals([
            ['A', 'B'], 
            [None, None],
            ['C', None],
            ['D', None],
            ['E', None],
        ], m.data)

        m.vspan('A', 'C')
        self.assertEquals([
            ['A', 'B', 'C'], 
            [None, None, None],
            [None, None, None],
            ['D', None, None],
            ['E', None, None],
        ], m.data)

        m.vspan('B', 'D')
        self.assertEquals([
            ['A', 'B', 'C', 'D'], 
            [None, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
            ['E', None, None, None],
        ], m.data)

        m.vspan('E', 'A')
        self.assertEquals([
            [None, 'B', 'C', 'D'], 
            [None, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
            ['E', 'A', None, None],
        ], m.data)


    def test_vspan_independent(self):
        """Test vertical span with independent requests 
        """
        m = SpanMatrix('A', 'B', 'C', 'D', 'E')

        m.vspan('A', 'B')
        m.vspan('C', 'D')
        self.assertEquals([
            ['A', 'B'], 
            [None, None],
            ['C', 'D'],
            [None, None],
            ['E', None],
        ], m.data)



class LayoutTestCase(unittest.TestCase):
    """
    Layout tests.
    """
    def test_default_simple(self):
        """Test default, simple alignment
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
""")
        ast = parse(f)
        c1 = ast.cache['c1']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']
        l.layout(ast)
        self.assertTrue(ast.data.get('align') is None)


    def test_default_span(self):
        """Test spanning of default, simple alignment
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"
""")
        ast = parse(f)
        c1 = ast.cache['c1']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']

        l.layout(ast)
        span, default = l._span_matrix(ast)

        self.assertEquals('middle', default.cls)
        self.assertEquals([c1, c2, c3], default.align)
        self.assertEquals([c1, c2, c3], default.span)

        self.assertEquals([[c1], [c2], [c3]], span.data)


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
        c1 = ast.cache['c1']
        c2 = ast.cache['c2']

        l._prepare(ast)
        align = ast.data['align']
        self.assertEquals(1, len(align))
        self.assertEquals('left', align[0].cls)
        self.assertEquals([c2, c1], align[0].align)
        self.assertEquals([c2, c1], align[0].span)

        span, default = l._span_matrix(ast, align)

        self.assertTrue(default is None)
        self.assertEquals([[None, None], [c2, c1]], span.data)


    def test_orphaned(self):
        """Test orphaned (due to alignment) elements
        """
        l = Layout()
        f = StringIO("""
class c1 "C1"
class c2 "C2"
class c3 "C3"

:layout:
    right: c1 c3
""")
        ast = parse(f)
        c1 = ast.cache['c1']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']

        l._prepare(ast)
        align = ast.data['align']
        self.assertEquals(1, len(align))
        self.assertEquals('right', align[0].cls)
        self.assertEquals([c1, c3], align[0].align)
        self.assertEquals([c1, c3], align[0].span)

        span, default = l._span_matrix(ast, align)

        self.assertEquals('middle', default.cls)
        self.assertEquals([c1, c2], default.align)
        self.assertEquals([c1, c2], default.span)

        self.assertEquals([
            [c1, c3],
            [c2, None],
            [None, None],
        ], span.data)


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
    center: c2 c3
""")
        ast = parse(f)
        c = ast.cache['c']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']
        c4 = ast.cache['c4']
        c5 = ast.cache['c5']

        l._prepare(ast)
        align = ast.data['align']
        self.assertEquals(1, len(align))
        self.assertEquals('center', align[0].cls)
        self.assertEquals([c2, c3], align[0].align)
        self.assertEquals([c, c3], align[0].span)

        span, default = l._span_matrix(ast, align)

        self.assertEquals('middle', default.cls)
        self.assertEquals([c, c4, c5], default.align)
        self.assertEquals([c, c4, c5], default.span)

        self.assertEquals([
            [c, c3],
            [None, None],
            [c4, None],
            [c5, None],
        ], span.data)


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
    left: a b
    right: d e
""")
        ast = parse(f)
        a = ast.cache['a']
        b = ast.cache['b']
        c = ast.cache['c']
        d = ast.cache['d']
        e = ast.cache['e']

        l._prepare(ast)
        align = ast.data['align']
        self.assertEquals(2, len(align))
        self.assertEquals('left', align[0].cls)
        self.assertEquals([a, b], align[0].align)
        self.assertEquals([a, b], align[0].span)
        self.assertEquals('right', align[1].cls)
        self.assertEquals([d, e], align[1].align)
        self.assertEquals([d, e], align[1].span)

        span, default = l._span_matrix(ast, align)

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
        """Test deep default align constraining with defined layout
        """
        l = Layout()
        # diagram:
        # -- c --
        # |c1 c2|
        # -------
        #  c3 c4
        #
        f = StringIO("""
class c "C"
    class c1 "C1"
    class c2 "C2"
class c3 "C3"
class c4 "C4"

:layout:
    right: c1 c3
    left: c2 c4
""")
        ast = parse(f)
        c = ast.cache['c']
        c1 = ast.cache['c1']
        c2 = ast.cache['c2']
        c3 = ast.cache['c3']
        c4 = ast.cache['c4']

        l._prepare(ast)
        align = ast.data['align']
        self.assertEquals(2, len(align))
        self.assertEquals('right', align[0].cls)
        self.assertEquals([c1, c3], align[0].align)
        self.assertEquals([c, c3], align[0].span)
        self.assertEquals('left', align[1].cls)
        self.assertEquals([c2, c4], align[1].align)
        self.assertEquals([c, c4], align[1].span)

        span, default = l._span_matrix(ast, align)

        self.assertTrue(default is None)

        self.assertEquals([
            [c, c3, c4],
            [None, None, None],
            [None, None, None],
        ], span.data)


# vim: sw=4:et:ai
