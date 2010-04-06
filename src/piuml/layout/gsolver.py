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
        pad = ps.padding
        self.add_lt(ns.ur.y, ps.ur.y, pad.top + ps.head + pad.top)
        self.add_lt(ns.ur.x, ps.ur.x, pad.right)
        self.add_lt(ps.ll.x, ns.ll.x, pad.left)

        # calculate height of compartments as packaged element is between
        # head and compartments
        #h = ps.size.height - (ps.head + pad.top + pad.bottom)
        #h = ps.size.height - ps.head
        h = pad.bottom
        self.add_lt(ps.ll.y, ns.ll.y, pad.bottom + h)


    def top(self, *nodes):
        def f(k1, k2):
            self.add_eq(k1.style.ur.y, k2.style.ur.y)
        self._apply(f, nodes)

    def bottom(self, *nodes):
        def f(k1, k2):
            self.add_eq(k1.style.ll.y, k2.style.ll.y)
        self._apply(f, nodes)

    def left(self, *nodes):
        def f(k1, k2):
            self.add_eq(k1.style.ll.x, k2.style.ll.x)
        self._apply(f, nodes)

    def right(self, *nodes):
        def f(k1, k2):
            self.add_eq(k1.style.ur.x, k2.style.ur.x)
        self._apply(f, nodes)

    def center(self, *nodes):
        def f(k1, k2):
            self.add_cl((k1.style.ll.x, k1.style.ur.x), (k2.style.ll.x, k2.style.ur.x))
        self._apply(f, nodes)

    def middle(self, *nodes):
        def f(k1, k2):
            self.add_cl((k1.style.ll.y, k1.style.ur.y), (k2.style.ll.y, k2.style.ur.y))
        self._apply(f, nodes)

    def hspan(self, *nodes):
        def f(k1, k2):
            m = k1.style.margin.right + k2.style.margin.left
            l = self.ast.data['edges'].get((k1.id, k2.id), 0)
            self.add_lt(k1.style.ur.x, k2.style.ll.x, max(l, m))
        self._apply(f, nodes)


    def vspan(self, *nodes):
        def f(k1, k2):
            m = k1.style.margin.bottom + k2.style.margin.top
            l = self.ast.data['edges'].get((k1.id, k2.id), 0)
            # span from top to bottom
            self.add_lt(k1.style.ll.y, k2.style.ur.y, max(l, m))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)


    def n_dependency(self, edge):
        t, h = edge.tail, edge.head
        self.ast.data['edges'][t.id, h.id] = 100
        self.ast.data['edges'][h.id, t.id] = 100

    n_generalization = n_dependency

# vim: sw=4:et:ai
