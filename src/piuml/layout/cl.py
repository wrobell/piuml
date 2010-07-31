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

from piuml.data import lca, lsb
from piuml.layout.solver import *
from piuml.data import Area, Node


class Layout(object):
    """
    Layout processing routines.

    :Attributes:
     ast
        piUML source parsed tree.
     edges
        Cache of edges with tail and head nodes as key.
    """
    def __init__(self):
        super(Layout, self).__init__()
        self.ast = None
        self.edges = {}


    def create(self, ast):
        """
        Postprocess align information.
        """
        self.ast = ast

        # postprocess align information to simplify layout constraints
        # assignment
        align = (n for n in self.ast.unwind() if n.type == 'align')
        for n in align:             # defined alignment
            self._defined_align(n)
        align = (n for n in self.ast.unwind() if n.is_packaging())
        for n in align:             # default alignment
            self._default_align(n)


    def layout(self, ast):
        """
        Create layout constraints.
        """
        F = {
            'diagram': self._node,
            'element': self._node,
            'edge': self._edge,
            'ielement': self._ielement,
        }
        # process in reversed order to constraint edges first
        for n in reversed(list(ast.unwind())):
            f = F.get(n.type)
            if f:
                f(n)


    def _ielement(self, node):
        nodes = []
        for e in node.data['lines']:
            p = lca(self.ast, e.tail, e.head)
            dist = lsb(p, [e.tail, e.head])
            self.hspan(dist[0], dist[1])
            if e.tail.element != node.element:
                nodes.append(e.tail)
            if e.head.element != node.element:
                nodes.append(e.head)
        self.between(node, nodes)


    def _defined_align(self, align):
        """
        Process specification of alignment of nodes and assign alignment
        information to their common parent (lca).
        """
        p = lca(self.ast, *align.data)

        dist = lsb(p, align.data)
        getattr(p.align, align.element).append(align.data)
        if align.element in ('top', 'middle', 'bottom'):
            p.align.hspan.append(dist)
        else: # left, center, right
            p.align.vspan.append(dist)


    def _default_align(self, node):
        """
        Set default alignment within specified, packaging node.

        :Parameters:
         node
            Packaging node.
        """
        packaged = [k for k in node if k.type == 'element']
        top, right, bottom, left, center, middle, hspan, vspan = node.align

        # summarize defined alignment
        defined = top + right + bottom + left + center + middle + hspan + vspan

        # unique set of node ids used in alignment definition
        done = set(id for k in defined for id in k)
        # list of non-aligned node ids
        default = [a for a in packaged if a not in done]

        # interleave non-aligned ids with the top of defined by user
        # alignment
        default.extend((v[0] for v in vspan))
        default.sort(key=packaged.index)
        middle.insert(0, default)
        hspan.insert(0, default)

        if __debug__:
            print node.id, 'default', default
            print node.id, 'top', top
            print node.id, 'right', right
            print node.id, 'bottom', bottom
            print node.id, 'left', left
            print node.id, 'center', center
            print node.id, 'middle', middle
            print node.id, 'hspan', hspan
            print node.id, 'vspan', vspan
            for align in node.align:
                for nodes in align:
                    assert not nodes or all(isinstance(k, Node) for k in nodes)


    def _node(self, node):
        """
        Constraint node and its children using alignment information.

        :Parameters:
         node
            Node to constraint.
        """
        self.size(node)
        if node.parent:
            self.within(node, node.parent)

        ns = node.style
        if node.is_packaging():
            # all the alignment functions...
            F = self.top, self.right, self.bottom, self.left, \
                self.center, self.middle, \
                self.hspan, self.vspan

            # ... are zipped with appropriate alignment information (top,
            # right, etc.)
            for f, align in zip(F, node.align):
                for nodes in align:
                    assert not nodes or all(isinstance(k, Node) for k in nodes)
                    f(*nodes)


    def _edge(self, edge):
        """
        Store edge minimal length in edge cache.

        :Parameters:
         edge
            Edge to constraint.
        """
        t, h = edge.tail, edge.head
        # fixme: there can be multiple edges
        length = edge.style.min_size[0]
        self.edges[t.id, h.id] = length
        self.edges[h.id, t.id] = length


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
        ps = parent.style
        pad = ps.padding

        # calculate height of compartments as packaged element is between
        # head and compartments
        head = ps.head + pad.top + pad.bottom
        h = ps.size.height - head
        cpad = Area(head + pad.top, # area pad.top
                pad.right,
                pad.bottom + h,     # area pad.bottom
                pad.left)
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
            l = self.edges.get((k1.id, k2.id), 0)
            self.add_c(MinHDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def vspan(self, *nodes):
        def f(k1, k2):
            m = k1.style.margin.bottom + k2.style.margin.top
            l = self.edges.get((k1.id, k2.id), 0)
            # span from top to bottom
            self.add_c(MinVDist(k2.style, k1.style, max(l, m)))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)

# vim: sw=4:et:ai
