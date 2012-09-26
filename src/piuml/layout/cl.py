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

from piuml.data import lca, lsb, MWalker, Relationship, \
    Element, PackagingElement
from piuml.layout.solver import *
from piuml.style import Area

from collections import namedtuple

import logging
log = logging.getLogger('piuml.layout.cl')

DefinedAlign = namedtuple('DefinedAlign', 'cls align')


class LayoutError(Exception):
    """
    Layout exception.
    """


class SpanMatrix(object):
    """
    Two dimensional matrix.

    The matrix is a list of lists organized in following manner::

              --       --
              | --- --- |
              | |A| |1| |
     m.data = |  B   2  |
              |  C   3  |
              | |D| |4| |
              | --- --- |
              --       --

    therefore, for example::

        m[0, 1] == B == m.data[0][1]
        m[1, 2] == 3 == m.data[1][2]

    """
    def __init__(self, *items):
        """
        Create span matrix with a row of items.

        :Parameters:
         items
            Items to be put in first row of span matrix, can be empty or
            null.
        """
        if items:
            self.data = [[d] for d in items]
        else:
            self.data = []


    def __getitem__(self, cell):
        (col, row) = cell
        return self.data[col][row]


    def __setitem__(self, cell, value):
        (col, row) = cell
        self.data[col][row] = value


    def insert_col(self, col):
        k = len(self.data[0]) if len(self.data) > 0 else 1
        self.data.insert(col, [None] * k)


    def insert_row(self, row):
        if self.data:
            for l in self.data:
                l.insert(row, None)
        else:
            self.data.append([None])


    def index(self, value):
        row = None
        for col, d in enumerate(self.data):
            try:
                row = d.index(value)
                break
            except ValueError:
                pass
                
        return None if row is None else (col, row)


    def dim(self):
        """
        Return span matrix dimensions.
        """
        return (len(self.data), len(self.data[0])) if self.data else (0, 0)


    def hspan(self, a, b):
        """
        Span two items horizontally.
        """
        pa = self.index(a)
        pb = self.index(b)
        if not pa or not pb:
            raise ValueError('One of arguments not found in span matrix')

        n, m = pa
        k, l = self.dim()
        self[pb] = None
        col = n + 1
        # find column, where 'b' can be put...
        while col < k and self[col, m] != None:
            col += 1
        # ... but if end of the span matrix, then add column
        if col == k:
            self.insert_col(col)
        self[col, m] = b


    def vspan(self, a, b):
        """
        Span two items vertically.
        """
        pa = self.index(a)
        pb = self.index(b)
        if not pa or not pb:
            raise ValueError('One of arguments not found in span matrix')

        n, m = pa
        k, l = self.dim()
        self[pb] = None
        row = m + 1
        # find row, where 'b' can be put...
        while row < l and self[n, row] != None:
            row += 1
        # ... but if end of the span matrix, then add row
        if row == l:
            self.insert_row(row)
        self[n, row] = b


    def columns(self):
        """
        Get list of columns.
        """
        return self.data


    def rows(self):
        """
        Get list of rows.
        """
        if len(self.data) > 0:
            m = len(self.data[0])
            return [[d[i] for d in self.data] for i in range(m)]
        else:
            return []


    def __str__(self):
        """
        Convert span matrix to a string.
        """
        return str(self.data)



class Layout(MWalker):
    """
    Layout processing routines.

    :Attributes:
     ast
        piUML source parsed tree.
     lines
        Cache of lines with tail and head nodes as key.
    """
    def __init__(self):
        super(Layout, self).__init__()
        self.ast = None
        self.lines = {}


    def layout(self, ast):
        """
        Layout diagram items on the diagram.
        """
        self.ast = ast # fixme
        self._create_line_cache()
        self._prepare(ast)

        # visit siblings in reversed order to constraint lines first
        self.preorder(ast, reverse=True)


    def _create_line_cache(self):
        """
        Find all lines and create line length cache.
        """
        lines = (l for l in self.ast if isinstance(l, Relationship))
        for l in lines:
            # find siblings
            t, h = l.tail, l.head
            t, h = self._level(t, h)

            length = self.lines.get((t.id, h.id), 0) 
            self.lines[t.id, h.id] = max(length, l.style.min_length)

            length = self.lines.get((h.id, t.id), 0) 
            self.lines[h.id, t.id] = max(length, l.style.min_length)


    def _prepare(self, ast):
        """
        Postprocess alignment information from parser and prepare alignment
        information for layout.
        """
        # all alignment is defined at this stage, therefore align
        # information can be assigned to appropriate nodes and
        # postprocessed to simplify layout constraints assignment
        align = (k for n in ast if n.name == 'layout' for k in n.data)

        # find common parent of nodes to align and put alignment
        # information on parent level
        for a in align:
            p = lca(self.ast, *a.nodes)

            if 'align' in p.data:
                data = p.data['align']
            else:
                data = p.data['align'] = []

            data.append(DefinedAlign(a.type, list(a.nodes)))


    def _level(self, *nodes):
        """
        Given the collection of nodes find all nodes having the same direct
        ancestor.
        """
        p = lca(self.ast, *nodes)
        return lsb(p, *nodes)


    def v_element(self, node):
        """
        Constraint element and its children using alignment information.

        :Parameters:
         node
            Node to constraint.
        """
        self.size(node)
        if node.parent:
            self.within(node, node.parent)

        ns = node.style
        if isinstance(node, PackagingElement):
            # first get the defined alignment
            align_info = node.data.get('align', [])

            # determine default alignment
            used_nodes = [n for align in align_info
                for n in self._level(*align.align)]
            default = DefinedAlign('middle', 
                [k for k in node
                if k not in used_nodes and type(k) in (Element, PackagingElement)])
                # fixme: if k not in used_nodes and k.can_align], [])

            if __debug__:
                log.debug('used nodes: {}'.format(used_nodes))
                log.debug('default align: {}'.format(default))
                log.debug('defined align: {}'.format(align_info))

            if default.align:
                # all alignment information determined
                align_info.insert(0, default)

            F = {
                'top': (self.top, self.hspan),
                'middle': (self.middle, self.hspan),
                'bottom': (self.bottom, self.hspan),
                'left': (self.left, self.vspan),
                'center': (self.center, self.vspan),
                'right': (self.right, self.vspan),
            }
            for align in align_info:
                nodes = align.align
                assert all(isinstance(k, Element) for k in nodes)

                # get alignment and span functions
                f_a, f_s = F[align.cls]
                f_a(*nodes)
                f_s(*self._level(*nodes))

    v_diagram = v_packagingelement = v_element

    def v_ielement(self, node):
        nodes = []
        left = None # find left node for hspan
        l_len = 0 # left side length
        right = None # find right node for hspan
        r_len = 0 # right side length

        # find nodes for alignment - the components in case of assembly
        for e in node.data['lines']:
            if e.head.cls != node.cls:
                if left is None:
                    left = e.head
                l_len = max(l_len, e.style.min_length)
                nodes.append(e.head)
            if e.tail.cls != node.cls:
                if right is None:
                    right = e.tail
                r_len = max(r_len, e.style.min_length)
                nodes.append(e.tail)

        p = lca(self.ast, left, right)
        left, right = lsb(p, left, right)
        self.lines[left.id, right.id] = r_len + l_len
        self.lines[right.id, left.id] = r_len + l_len

        self.between(node, nodes)


    def size(self, node):
        """
        Set node minimum size.
        """


    def within(self, parent, node):
        """
        Constraint node to be contained within parent.
        """


    def between(self, node, nodes):
        """
        Constraint node to be between other nodes.
        """


    def top(self, *nodes):
        """
        Align nodes on the top.
        """


    def bottom(self, *nodes):
        """
        Align nodes on the bottom.
        """


    def left(self, *nodes):
        """
        Align nodes on the left.
        """


    def right(self, *nodes):
        """
        Align nodes on the right.
        """


    def center(self, *nodes):
        """
        Center horizontally all nodes.
        """


    def middle(self, *nodes):
        """
        Center vertically all nodes.
        """


    def hspan(self, *nodes):
        """
        Span nodes horizontally.
        """


    def vspan(self, *nodes):
        """
        Span nodes vertically.
        """



class ConstraintLayout(Layout):
    def __init__(self):
        super(ConstraintLayout, self).__init__()
        self.solver = Solver()

    def add_c(self, c):
        self.solver.add(c)


    def layout(self, ast):
        super(ConstraintLayout, self).layout(ast)
        self.solver.solve()


    def size(self, node):
        self.add_c(MinSize(node.style))


    def within(self, node, parent):
        ns = node.style
        mar = ns.margin
        ps = parent.style
        pad = ps.padding

        # put packaged elements between head and rest of compartements 
        top = ps.compartment[0] + pad.top + pad.bottom
        bottom = ps.min_size.height - (top + pad.bottom)

        top = max(mar.top, top)
        right = max(mar.right, pad.right)
        bottom = max(mar.bottom, bottom)
        left = max(mar.left, pad.left)

        cpad = Area(top, right, bottom, left)
        self.add_c(Within(ns, ps, cpad))


    def between(self, node, nodes):
        ns = node.style
        others = [n.style for n in nodes]
        self.add_c(Between(ns, others))


    def top(self, *nodes):
        def f(k1, k2):
            self.add_c(TopEq(k1.style, k2.style))
        self._apply(f, nodes)

    def bottom(self, *nodes):
        def f(k1, k2):
            self.add_c(BottomEq(k1.style, k2.style))
        self._apply(f, nodes)

    def middle(self, *nodes):
        def f(k1, k2):
            self.add_c(MiddleEq(k1.style, k2.style))
        self._apply(f, nodes)

    def left(self, *nodes):
        def f(k1, k2):
            self.add_c(LeftEq(k1.style, k2.style))
        self._apply(f, nodes)

    def right(self, *nodes):
        def f(k1, k2):
            self.add_c(RightEq(k1.style, k2.style))
        self._apply(f, nodes)

    def center(self, *nodes):
        def f(k1, k2):
            self.add_c(CenterEq(k1.style, k2.style))
        self._apply(f, nodes)


    def hspan(self, *nodes):
        def f(k1, k2):
            m = k1.style.margin.right + k2.style.margin.left
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinHDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def vspan(self, *nodes):
        def f(k1, k2):
            m = k1.style.margin.bottom + k2.style.margin.top
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinVDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)

# vim: sw=4:et:ai
