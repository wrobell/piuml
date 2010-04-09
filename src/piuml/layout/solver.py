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

import time
import math
from collections import deque

from piuml.layout import PreLayout
from piuml.data import Size, Style, Area

EPSILON = 1


class Constraint(object):
    """
    Basic class for all constraints.

    A constraint is a callable. When called it finds solution and returns
    list of variables, which changed due solution calculation.

    :Attributes:
     variables
        List of variables being manipulated by a constraint.
    """
    def __init__(self):
        super(Constraint, self).__init__()
        self.variables = []


    def __call__(self):
        """
        Find solution for constraint's variables and return changed
        variables.
        """
        raise NotImplemented('Constraint solution not implemented')


class CenterLinesConstraint(Constraint):
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


class MinSizeConstraint(Constraint):
    """
    Rectangle minimal size constraint.
    """
    def __init__(self, r):
        super(MinSizeConstraint, self).__init__()
        self.r = r
        self.variables = [r]


    def __call__(self):
        changed = []
        r = self.r
        w, h = r.min_size
        pad = r.padding
        w += pad.left + pad.right
        h += pad.top + pad.bottom
        if r.ur.x - r.ll.x < w:
            #r.ur.x = r.ll.x + w
            r.ur.x += 10
            changed = [r]
        if r.ur.y - r.ll.y < h:
            #r.ur.y = r.ur.y + h
            r.ur.y += 10
            changed = [r]
        return changed


class RectConstraint(Constraint):
    """
    Abstract constraint to align two rectangles.

    :Attributes:
     a
        First rectangle.
     b
        Second rectangle
    """
    def __init__(self, a, b):
        super(RectConstraint, self).__init__()
        self.a = a
        self.b = b
        self.variables = [a, b]


class TopEq(RectConstraint):
    """
    Constraint to maintain top edges of two rectangles at the same
    position.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ur.y < b.ur.y:
            h = a.size.height
            a.ur.y = b.ur.y
            a.ll.y = a.ur.y - h
            changed = [a]
        if a.ur.y > b.ur.y:
            h = b.size.height
            b.ur.y = a.ur.y
            b.ll.y = b.ur.y - h
            changed = [b]
        return changed


class BottomEq(RectConstraint):
    """
    Constraint to maintain bottom edges of two rectangles at the same
    position.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ll.y < b.ll.y:
            h = a.size.height
            a.ll.y = b.ll.y
            a.ur.y = a.ll.y + h
            changed = [a]
        if a.ll.y > b.ll.y:
            h = b.size.height
            b.ll.y = a.ll.y
            b.ur.y = b.ll.y + h
            changed = [b]
        return changed



class LeftEq(RectConstraint):
    """
    Constraint to maintain left edges of two rectangles at the same
    position.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ll.x < b.ll.x:
            w = a.size.width
            a.ll.x = b.ll.x
            a.ur.x = a.ll.x + w
            changed = [a]
        if a.ll.x > b.ll.x:
            w = b.size.width
            b.ll.x = a.ll.x
            b.ur.x = b.ll.x + w
            changed = [b]
        return changed



class RightEq(RectConstraint):
    """
    Constraint to maintain right edges of two rectangles at the same
    position.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ur.x < b.ur.x:
            w = a.size.width
            a.ur.x = b.ur.x
            a.ll.x = a.ur.x - w
            changed = [a]
        if a.ur.x > b.ur.x:
            w = b.size.width
            b.ur.x = a.ur.x
            b.ll.x = b.ur.x - w
            changed = [b]
        return changed


class MinDistConstraint(RectConstraint):
    """
    Abstract constraint for minimal distance between two rectangles.

    :Attributes:
     dist
        The distance to maintain.
    """
    def __init__(self, a, b, dist):
        super(MinDistConstraint, self).__init__(a, b)
        self.dist = dist


class MinHDist(MinDistConstraint):
    """
    Constraint to maintain minimal horizontal distance between two
    rectangles.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ur.x + self.dist > b.ll.x:
            w = b.size.width
            b.ll.x = a.ur.x + self.dist
            b.ur.x = b.ll.x + w # keep current width of rectangle
            changed = [b]
        return changed


class MinVDist(MinDistConstraint):
    """
    Constraint to maintain minimal vertical distance between two
    rectangles.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.ur.y + self.dist > b.ll.y:
            h = b.size.height
            b.ll.y = a.ur.y + self.dist
            b.ur.y = b.ll.y + h # keep current height of rectangle
            changed = [b]
        return changed


class Within(Constraint):
    """
    Keep two rectangles within each other using specified padding.

    :Attributes:
     kid
        Rectangle contained within parent rectangle.
     parent
        Parent rectangle containing the kid.
     pad
        Padding information (tuple: top, right, bottom, left).
    """
    def __init__(self, kid, parent, pad):
        self.parent = parent
        self.kid = kid
        self.pad = pad
        self.variables = [parent, kid]


    def __call__(self):
        changed = set()
        p = self.parent
        k = self.kid
        pad = self.pad
        if p.ll.x + pad.left > k.ll.x:
            w = k.size.width
            k.ll.x = p.ll.x + pad.left
            k.ur.x = k.ll.x + w
            changed.add(k)
        if k.ur.x + pad.right > p.ur.x:
            p.ur.x = k.ur.x + pad.right
            changed.add(p)
        if p.ll.y + pad.bottom > k.ll.y:
            h = k.size.height
            k.ll.y = p.ll.y + pad.bottom
            k.ur.y = k.ll.y + h
            changed.add(k)
        if k.ur.y + pad.top > p.ur.y:
            p.ur.y = k.ur.y + pad.top
            changed.add(p)
        return changed


class Solver(object):
    """
    Constraint solver.

    :Attributes:
     _constraints
        List of constraints.
     _dep
        Dependencies between constraints.
    """
    def __init__(self):
        self._constraints = []
        self._deps = {}


    def add(self, c):
        """
        Add a constraint to constraint solver.

        Constraint's variables are used to build dependency cache.
        """
        self._constraints.append(c)
        for d in c.variables:
            if d in self._deps:
                deps = self._deps[d]
            else:
                deps = self._deps[d] = set()
            deps.add(c)


    def solve(self):
        """
        Find solution for all constraints.
        """
        # deque with set properties would be nice...
        unsolved = deque(self._constraints)
        inque = set(self._constraints)

        t1 = time.time()

        self.count = 0 # count of constraint solving events, if too many,
                       # then bail out to avoid cpu hog
        kill = len(self._constraints) ** 2 # we won't accept O(n^2)
        while unsolved:
            
            c = unsolved.popleft()    # get a constraint to solve...
            inque.remove(c)
            variables = c()           # ... and find solution

            # if a variable is changed, then push dependant constraints to
            # solve again
            for v in variables:
                deps = self._deps.get(v, set())

                # skip constraints already being in unsolved queue
                to_solve = deps - inque

                unsolved.extend(to_solve)
                inque.update(to_solve)

            self.count += 1
            if self.count > kill:
                raise ValueError('Could not solve' \
                        '; unsolved=%d after %d iterations' \
                    % (len(unsolved), self.count))

        assert len(unsolved) == 0

        # some stats follows
        t2 = time.time()
        k = len(self._constraints)
        fmt = 'k=constraints: {k}, steps: {c}, O(k log k)={O}, time: {t:.3f}'
        print fmt.format(k=k, c=self.count, O=int(math.log(k, 2) * k), t=t2 -t1)



class ConstraintLayout(PreLayout):
    def __init__(self):
        PreLayout.__init__(self)
        self.solver = Solver()

    def add_c(self, c):
        self.solver.add(c)


    def layout(self, ast):
        PreLayout.layout(self, ast)
        self.solver.solve()


    def size(self, node):
        self.add_c(MinSizeConstraint(node.style))


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
            self.add_c(TopEq(k1.style, k2.style))
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
            self.add_c(LeftEq(k1.style, k2.style))
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
