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

from piuml.layout import PreLayout
from piuml.data import Size
from gaphas import solver
from gaphas import constraint as ct



class CenterLinesConstraint(ct.Constraint):
    def __init__(self, l1=None, l2=None):
        super(CenterLinesConstraint, self).__init__(l1[0], l1[1], l2[0], l2[1])
        self.l1 = l1
        self.l2 = l2

    def solve_for(self, var):
        l1 = self.l1
        l2 = self.l2
        if var in l2:
            l1, l2 = l2, l1
        w1 = l1[1].value - l1[0].value
        w2 = l2[1].value - l2[0].value
        v1 = l1[0].value + w1 / 2
        v2 = l2[0].value + w2 / 2
        if abs(v1 - v2) > 1e-6:
            v1 = max(v1, v2)
            l1[0].value = v1 - w1 / 2
            l1[1].value = v1 + w1 / 2
            l2[0].value = v1 - w2 / 2
            l2[1].value = v1 + w2 / 2

class LessThanConstraint(ct.Constraint):
    def __init__(self, smaller=None, bigger=None, delta=1.0):
        super(LessThanConstraint, self).__init__(smaller, bigger)
        self.smaller = smaller
        self.bigger = bigger
        self.delta = delta

    def solve_for(self, var):
        if self.smaller.value >= self.bigger.value - self.delta:
            self.bigger.value = self.smaller.value + self.delta


class ConstraintLayout(PreLayout):
    def __init__(self):
        PreLayout.__init__(self)
        self.solver = solver.Solver()

    def add_lt(self, *args):
        self.solver.add_constraint(LessThanConstraint(*args))

    def add_eq(self, *args):
        self.solver.add_constraint(ct.EqualsConstraint(*args))

    def add_c(self, *args):
        self.solver.add_constraint(ct.CenterConstraint(*args))

    def add_cl(self, *args):
        self.solver.add_constraint(CenterLinesConstraint(*args))


    def layout(self, ast):
        ast.style.size = Size(1000, 1000)
        PreLayout.layout(self, ast)
        self.solver.solve()


    def size(self, node):
        ns = node.style
        self.add_lt(ns.ll.x, ns.ur.x, ns.size.width)
        self.add_lt(ns.ll.y, ns.ur.y, ns.size.height)


    def within(self, parent, node):
        ns = node.style
        ps = parent.style
        self.add_lt(ps.ll.x, ns.ll.x, ps.padding.left)
        self.add_lt(ns.ur.x, ps.ur.x, ps.padding.right)
        self.add_lt(ps.ll.y, ns.ll.y, ps.size.height)
        self.add_lt(ns.ur.y, ps.ur.y, ps.padding.bottom)

    def top(self, *nodes):
        def f(k1s, k2s):
            self.add_eq(k1s.ur.y, k2s.ur.y)
        self._apply(f, nodes)

    def bottom(self, *nodes):
        def f(k1s, k2s):
            self.add_eq(k1s.ll.y, k2s.ll.y)
        self._apply(f, nodes)

    def left(self, *nodes):
        def f(k1s, k2s):
            self.add_eq(k1s.ll.x, k2s.ll.x)
        self._apply(f, nodes)

    def right(self, *nodes):
        def f(k1s, k2s):
            self.add_eq(k1s.ur.x, k2s.ur.x)
        self._apply(f, nodes)

    def center(self, *nodes):
        def f(k1s, k2s):
            self.add_cl((k1s.ll.x, k1s.ur.x), (k2s.ll.x, k2s.ur.x))
        self._apply(f, nodes)

    def middle(self, *nodes):
        def f(k1s, k2s):
            self.add_cl((k1s.ll.y, k1s.ur.y), (k2s.ll.y, k2s.ur.y))
        self._apply(f, nodes)

    def hspan(self, *nodes):
        def f(k1s, k2s):
            d = k1s.margin.right + k2s.margin.left
            self.add_lt(k1s.ur.x, k2s.ll.x, d)
        self._apply(f, nodes)

    def vspan(self, *nodes):
        def f(k1s, k2s):
            d = k1s.margin.bottom + k2s.margin.top
            # span from top to bottom
            self.add_lt(k1s.ll.y, k2s.ur.y, d)
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1.style, k2.style)


    def n_dependency(self, edge):
        ts = edge.tail.style
        hs = edge.head.style
        p1, p2 = edge.style.edges
#        self.add_lt(p1.x, ur.x, 100)
        self.add_eq(ts.ur.x, p1.x)
        self.add_c(ts.ll.y, ts.ur.y, p1.y)
        self.add_eq(hs.ll.x, p2.x)
        self.add_c(hs.ll.y, hs.ur.y, p2.y)

    n_commentline = n_connector = n_generalization = n_association \
        = n_dependency

# vim: sw=4:et:ai
