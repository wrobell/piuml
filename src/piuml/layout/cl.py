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
    Element, PackagingElement, NodeGroup
from piuml.layout.solver import *
from piuml.style import Area

from collections import OrderedDict
import logging
log = logging.getLogger('piuml.layout.cl')


class LayoutError(Exception):
    """
    Layout exception.
    """


class Layout(object):
    """
    Layout processor.

    :Attributes:
     ast
        piUML source parsed tree.
     align
        Cache of alignment information per nodes common parent.
     lines
        Cache of lines with tail and head nodes as key.
    """
    def __init__(self, ast):
        """
        Create layout processor.
        """
        super(Layout, self).__init__()
        self.ast = ast
        self.align = OrderedDict()
        self.lines = {}
        self.solver = Solver()


    def layout(self, solve=True):
        """
        Layout diagram items on the diagram.

        :Parameters:
         solve
            Do not solve constraints if False (useful for layout unit
            testing).
        """
        dab = DefaultAlignBuilder(self)
        cb = ConstraintBuilder(self)

        self._create_align_cache()
        dab.preorder(self.ast, reverse=True) # find default alignment
        self._create_align_groups()
        self._create_line_cache()
        cb.preorder(self.ast, reverse=True)  # create constraints
        if solve:
            self.solver.solve()


    def _create_line_cache(self):
        """
        Find all lines and create line length cache.
        """
        lines = (l for l in self.ast if isinstance(l, Relationship))
        for l in lines:
            # find siblings
            t, h = l.tail, l.head
            t, h = level(self.ast, t, h)

            length = self.lines.get((t.id, h.id), 0) 
            self.lines[t.id, h.id] = max(length, l.style.min_length)

            length = self.lines.get((h.id, t.id), 0) 
            self.lines[h.id, t.id] = max(length, l.style.min_length)


    def _create_align_cache(self):
        """
        Create alignment information cache - the aligment information is
        groupped by common nodes parent.
        """
        align = (k for n in self.ast if n.name == 'layout' for k in n.data)

        for a in align:
            p = lca(self.ast, *a.nodes)
            if p not in self.align:
                self.align[p] = []
            self.align[p].append(a)


    def _create_align_groups(self):
        # default align only? leave it alone
        all_align = [(p, a) for p, a in self.align.items() if len(a) > 1]
        for p, align_info in all_align:
            for a in list(align_info):
                p = lca(p, *a.nodes)
                nodes = lsb(p, *a.nodes)
                log.debug('{} -> {}'.format(tuple(n.id for n in a.nodes), tuple(n.id for n in nodes)))

                # fixme: reparent function?
                log.debug('remove {} from {}'.format(tuple(n.id for n in nodes), p.id))
                for n in nodes:
                    p.children.remove(n)
                    n.parent = None

                log.debug('append {} to {}'.format(tuple(n.id for n in nodes), a.id))
                ng = NodeGroup(a.id, children=nodes)
                # fixme: reparent function?
                ng.parent = p
                p.children.append(ng)
                log.debug('{} added to {}'.format(ng.id, p.id))

                #self.align[ng] = [a]
                #align_info.remove(a)
                #if len(align_info) == 0:
                #    del self.align[p]


class DefaultAlignBuilder(MWalker):
    """
    Default align builder.

    Walks through the piUML's AST and updates alignment cache with default
    alignment definition.

    :Attributes:
     ast
        piUML's AST.
     align
        Alignment cache.
    """
    def __init__(self, layout):
        """
        Create default alignment builder for the layout.
        """
        self.ast = layout.ast
        self.align = layout.align


    def v_packagingelement(self, node):
        """
        Update alignment cache with default alignment information.

        :Parameters:
         node
            The node for which default alignment has to be found.
        """
        # get all alignment info
        if node not in self.align:
            self.align[node] = []

        align_info = self.align[node]

        used_nodes = set()
        for a in align_info:
            v = level(node, *a.nodes)
            if not used_nodes & set(v):
                v = v[1:]
            used_nodes.update(v)

        default = Align('middle')
        default.nodes = [k for k in node
            if k not in used_nodes and type(k) in (Element, PackagingElement)]
            # fixme: if k not in used_nodes and k.can_align], [])

        if __debug__:
            log.debug('{} used nodes: {}'.format(node.id, used_nodes))
            log.debug('{} default align: {}'.format(node.id, default))
            log.debug('{} defined align: {}'.format(node.id, align_info))

        if len(default.nodes) > 1:
            # all alignment information determined
            align_info.insert(0, default)

    v_diagram = v_packagingelement



class ConstraintBuilder(MWalker):
    def __init__(self, layout):
        """
        Create constraints builder for the layout.
        """
        super(ConstraintBuilder, self).__init__()
        self.ast = layout.ast
        self.solver = layout.solver
        self.align = layout.align
        self.lines = layout.lines


    def _align_nodes(self, node):
        """
        Align children of the node.
        
        The default children alignment is determined. The children are
        aligned using both default and user defined alignment information.
        """
        align_info = self.align.get(node, [])

        for a in align_info:
            if __debug__:
                assert all(isinstance(k, Element) for k in a.nodes)
                assert a.type in ALIGN_CONSTRAINTS

            # get alignment and span functions
            f_a, f_s = ALIGN_CONSTRAINTS[a.type]
            f_a(self, *a.nodes)
            f_s(self, *level(node, *a.nodes))


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

    v_nodegroup = v_diagram = v_packagingelement = v_element

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

        left, right = level(self.ast, left, right)
        self.lines[left.id, right.id] = r_len + l_len
        self.lines[right.id, left.id] = r_len + l_len

        self.between(node, nodes)


    def add_c(self, c):
        self.solver.add(c)


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
            assert k1 is not k2, '{} vs. {}'.format(k1, k2)
            m = k1.style.margin.right + k2.style.margin.left
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinHDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def vspan(self, *nodes):
        def f(k1, k2):
            if __debug__:
                log.debug('{} vspan {}'.format(k1.id, k2.id))
            assert k1 is not k2, '{} vs. {}'.format(k1, k2)
            m = k1.style.margin.bottom + k2.style.margin.top
            l = self.lines.get((k1.id, k2.id), 0)
            self.add_c(MinVDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)


# map align types to ConstraintBuilder methods 
ALIGN_CONSTRAINTS = {
    'top': (ConstraintBuilder.top, ConstraintBuilder.hspan),
    'middle': (ConstraintBuilder.middle, ConstraintBuilder.hspan),
    'bottom': (ConstraintBuilder.bottom, ConstraintBuilder.hspan),
    'left': (ConstraintBuilder.left, ConstraintBuilder.vspan),
    'center': (ConstraintBuilder.center, ConstraintBuilder.vspan),
    'right': (ConstraintBuilder.right, ConstraintBuilder.vspan),
}


def level(ast, *nodes):
    """
    Given the collection of nodes find all nodes having the same direct
    ancestor.
    """
    p = lca(ast, *nodes)
    return lsb(p, *nodes)


# vim: sw=4:et:ai
