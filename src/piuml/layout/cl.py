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

from piuml.data import lca, lsb, MWalker, Align, Relationship, \
    Element, PackagingElement
from piuml.layout.solver import *
from piuml.style import Area

import logging
log = logging.getLogger('piuml.layout.cl')


class LayoutError(Exception):
    """
    Layout exception.
    """


class Layout(MWalker):
    """
    Layout processing routines.

    :Attributes:
     ast
        piUML source parsed tree.
     align
        Cache of alignment information per nodes common parent.
     lines
        Cache of lines with tail and head nodes as key.
    """
    def __init__(self):
        super(Layout, self).__init__()
        self.ast = None
        self.align = {}
        self.lines = {}


    def layout(self, ast):
        """
        Layout diagram items on the diagram.
        """
        self.ast = ast # fixme
        self._create_align_cache(ast)
        self._create_line_cache()

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


    def _create_align_cache(self, ast):
        """
        Create alignment information cache - the aligment information is
        groupped by common nodes parent.
        """
        align = (k for n in ast if n.name == 'layout' for k in n.data)

        for a in align:
            p = lca(self.ast, *a.nodes)
            if p not in self.align:
                self.align[p] = []
            self.align[p].append(a)


    def _level(self, *nodes):
        """
        Given the collection of nodes find all nodes having the same direct
        ancestor.
        """
        p = lca(self.ast, *nodes)
        return lsb(p, *nodes)


    def _align_nodes(self, node):
        """
        Align children of the node.
        
        The default children alignment is determined. The children are
        aligned using both default and user defined alignment information.
        """
        # get user defined alignment
        align_info = self.align.get(node, [])[:]

        # determine default alignment
        used_nodes = set()
        for a in align_info:
            v = lsb(node, *a.nodes)
            if not used_nodes & set(v):
                v = v[1:]
            used_nodes.update(v)

        default = Align('middle')
        default.nodes = [k for k in node
            if k not in used_nodes and type(k) in (Element, PackagingElement)]
            # fixme: if k not in used_nodes and k.can_align], [])

        if __debug__:
            log.debug('used nodes: {}'.format(used_nodes))
            log.debug('default align: {}'.format(default))
            log.debug('defined align: {}'.format(align_info))

        if len(default.nodes) > 1:
            # all alignment information determined
            align_info.insert(0, default)

        for a in align_info:
            if __debug__:
                assert all(isinstance(k, Element) for k in a.nodes)
                assert a.type in ALIGN_CONSTRAINTS

            # get alignment and span functions
            f_a, f_s = ALIGN_CONSTRAINTS[a.type]
            f_a(self, *a.nodes)
            f_s(self, *lsb(node, *a.nodes))


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

        if isinstance(node, PackagingElement):
            self._align_nodes(node)

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

        left, right = self._level(self.ast, left, right)
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
        if __debug__:
            log.debug('{} within {}'.format(node.id, parent.id))
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
            if __debug__:
                log.debug('{} at top {}'.format(k1.id, k2.id))
            self.add_c(TopEq(k1.style, k2.style))
        self._apply(f, nodes)

    def bottom(self, *nodes):
        def f(k1, k2):
            if __debug__:
                log.debug('{} bottom {}'.format(k1.id, k2.id))
            self.add_c(BottomEq(k1.style, k2.style))
        self._apply(f, nodes)

    def middle(self, *nodes):
        def f(k1, k2):
            if __debug__:
                log.debug('{} middle {}'.format(k1.id, k2.id))
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
            if __debug__:
                log.debug('{} hspan {}'.format(k1.id, k2.id))
            assert k1 is not k2
            m = k1.style.margin.right + k2.style.margin.left
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinHDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def vspan(self, *nodes):
        def f(k1, k2):
            if __debug__:
                log.debug('{} vspan {}'.format(k1.id, k2.id))
            assert k1 is not k2
            m = k1.style.margin.bottom + k2.style.margin.top
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinVDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)


# map align types to ConstraintLayout methods 
ALIGN_CONSTRAINTS = {
    'top': (ConstraintLayout.top, ConstraintLayout.hspan),
    'middle': (ConstraintLayout.middle, ConstraintLayout.hspan),
    'bottom': (ConstraintLayout.bottom, ConstraintLayout.hspan),
    'left': (ConstraintLayout.left, ConstraintLayout.vspan),
    'center': (ConstraintLayout.center, ConstraintLayout.vspan),
    'right': (ConstraintLayout.right, ConstraintLayout.vspan),
}

# vim: sw=4:et:ai
