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
from piuml.data import Size, Style, Area
from collections import deque

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


def rect(self):
    """
    Rectangle constraint. It maintains minimal size of a rectangle.
    
    Rectangle constraint is a wrapper around node's style object (from
    piUML language data model) and it could be any generic rectangle.
    """
    changed = []
    w, h = self.min_size
    if self.ur.x - self.ll.x < w:
        self.ur.x += 10 #w + pad.left + pad.right
        changed = [self]
    if self.ur.y - self.ll.y < h:
        self.ur.y += 10 #h + pad.top + pad.bottom
        changed = [self]
    return changed


# bind rectangle constraint to Style class to maintain node rectangle
# properties
Style.__call__ = rect
Style.variables = property(lambda s: [])


class TopEq(Constraint):
    """
    Constraint to maintain top edges of two rectangles at the same
    position.

    :Attributes:
     a
        First rectangle.
     b
        Second rectangle
    """
    def __init__(self, a, b):
        super(TopEq, self).__init__()
        self.a = a
        self.b = b
        self.variables = [a, b]


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



class LeftEq(Constraint):
    """
    Constraint to maintain left edges of two rectangles at the same
    position.

    :Attributes:
     a
        First rectangle.
     b
        Second rectangle
    """
    def __init__(self, a, b):
        super(LeftEq, self).__init__()
        self.a = a
        self.b = b
        self.variables = [a, b]


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


class MinHDist(Constraint):
    """
    Constraint to maintain minimal horizontal distance between two
    rectangles.

    :Attributes:
     a
        First rectangle.
     b
        Second rectangle
     dist
        The distance to maintain.
    """
    def __init__(self, a, b, dist):
        self.a = a
        self.b = b
        self.dist = dist
        self.variables = [a, b]

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


class MinVDist(Constraint):
    """
    Constraint to maintain minimal vertical distance between two
    rectangles.

    :Attributes:
     a
        First rectangle.
     b
        Second rectangle
     dist
        The distance to maintain.
    """
    def __init__(self, a, b, dist):
        self.a = a
        self.b = b
        self.dist = dist
        self.variables = [a, b]

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
        unsolved = deque(self._constraints)
        inque = set(self._constraints)

        self.count = 0
        import time
        t1 = time.time()
        while unsolved:
            # get constraint to solve...
            c = unsolved.popleft()     # get constraint to solve
            # and find solution
            changed = c()
            inque.remove(c)

            # if a variable is modified, then push dependencies to solve
            # again
            for m in changed:
                deps = self._deps.get(m, set())
                # skip constraints already being in unsolved queue
                to_solve = deps - inque
                unsolved.extend(to_solve)
                inque.update(to_solve)

            self.count += 1
            if self.count > len(self._constraints) ** 2:
                raise ValueError('Could not solve; unsolved=%d after %d iterations' % (len(unsolved), self.count))
        assert len(unsolved) == 0
        t2 = time.time()
        k = len(self._constraints)
        import math
        print 'steps: ', self.count, k, 2 * math.log(k, 2) * k, '%ss' % (t2 - t1)



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
        self.add_c(node.style)


    def within(self, node, parent):
        ns = node.style
        ps = parent.style
        pad = ps.padding

        # calculate height of compartments as packaged element is between
        # head and compartments
        h = ps.size.height - (ps.head + pad.top + pad.bottom)
        print node.id, node.type, node.element, 'h', h, ps.size.height, ps.head
        #h = ps.size.height - ps.head
        #h = pad.bottom
        #h = 0
        cpad = Area(pad.top + ps.head + pad.bottom,
                pad.right,
                pad.bottom + h,
                pad.left)
        self.add_c(Within(ns, ps, cpad))


    def top(self, *nodes):
        def f(k1, k2):
            self.add_c(TopEq(k1.style, k2.style))
        self._apply(f, nodes)

    def bottom(self, *nodes):
        def f(k1, k2):
            self.add_c(TopEq(k1.style, k2.style))
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
            self.add_c(LeftEq(k1.style, k2.style))
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
            #self.add_c(MinVDist(k2.style, k1.style, max(l, m)))
            self.add_c(MinVDist(k1.style, k2.style, max(l, m)))
        self._apply(f, nodes)


    def _apply(self, f, node):
        for k1, k2 in zip(node[:-1], node[1:]):
            f(k1, k2)

# vim: sw=4:et:ai