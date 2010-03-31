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

#from piuml.layout.gv import GVGraph as Layout

from spark import GenericASTTraversal
from piuml.parser import unwind
from piuml.data import lca

class PreLayout(GenericASTTraversal):
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self.ast = None
        self.nodes = None

    def create(self, ast):
        """
        Postprocess align information.
        """
        self.ast = ast

        # build the index cache
        self.nodes = dict(((k.id, k) for k in unwind(self.ast)))

        # postprocess align information to simplify layout constraints
        # assignment
        align = (n for n in unwind(self.ast) if n.type == 'align')
        for n in align:             # defined alignment
            self._defined_align(n)
        align = (n for n in unwind(self.ast) if n.is_packaging())
        for n in align:             # default alignment
            self._default_align(n)


    def layout(self, ast):
        """
        Create layout constraints.
        """
        self.postorder(ast)

    def n_diagram(self, node):
        self._constraint(node)

    def n_element(self, node):
        self._constraint(node)


    def _defined_align(self, align):
        """
        Process specification of alignment of nodes and assign alignment
        information to their common parent (lca).
        """
        ids = [n.id for n in align.data]
        p = lca(self.ast, *(n for n in align.data))

        def span(ids):
            span = []
            for id in ids:
                k = self.nodes[id]
                # k at least 2 levels lower
                if k.parent.id != p.id:
                    pp = k.parent
                    while pp.parent.id != p.id:
                        pp = pp.parent
                    span.append(pp.id)
                else:
                    span.append(id)
            return span

        if 'top' in align.element:
            p.align.top.append(ids[:])
            p.align.hspan.append(span(ids[:]))
        elif 'left' in align.element:
            p.align.left.append(ids[:])
            p.align.vspan.append(span(ids[:]))


    def _default_align(self, node):
        """
        Set default alignment within specified, packaging node.

        :Parameters:
         node
            Packaging node.
        """
        packaged = [k.id for k in node if k.type == 'element']
        top, right, bottom, left, center, middle, hspan, vspan = node.align

        # summarize defined alignment
        defined = top + right + bottom + left + center + middle + hspan + vspan

        # unique set of node ids used in alignment definition
        done = set(id for k in defined for id in k)
        # list of non-aligned node ids
        lost = [a for a in packaged if a not in done]

        # set default layout for non aligned node ids,
        # which is: span horizontally, center vertically
        if len(lost) == 1 and len(middle) == 0 and len(center) > 0:
            center[0].extend(lost)
            vspan[0].extend(lost)
        elif len(lost) > 1 and len(middle) > 0:
            middle[0].extend(lost)
            hspan[0].extend(lost)
        elif len(lost) > 1:
            middle.append(lost)
            hspan.append(lost)

        if __debug__:
            print node.id, 'top', top
            print node.id, 'right', right
            print node.id, 'bottom', bottom
            print node.id, 'left', left
            print node.id, 'center', center
            print node.id, 'middle', middle
            print node.id, 'hspan', hspan
            print node.id, 'vspan', vspan


    def _constraint(self, node):
        """
        Constraint the node and its children using alignment information.

        :Parameters:
         node
            Node to constraint.
        """
        self.size(node)
        if node.parent:
            self.within(node.parent, node)

        ns = node.style
        if node.is_packaging():
            f = self.top, self.right, self.bottom, self.left, \
                self.center, self.middle, \
                self.hspan, self.vspan

            for f, data in zip(f, node.align):
                for ids in data:
                    nodes = [self.nodes[id] for id in ids]
                    f(*nodes)


    def size(self, node):
        """
        Set node minimum size.
        """

    def within(self, parent, node):
        """
        Constraint node to be contained within parent.
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


from piuml.layout.gsolver import ConstraintLayout as Layout

# vim: sw=4:et:ai
