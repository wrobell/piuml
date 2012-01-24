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

"""
Simple constraint solver to solve constraints related to rectangles
alignment (minimal size, position, containment, etc.).

A rectangle has to implement following interface

    interface rec 'Rectangle'
        : pos: Pos      # rectangle position
        : size: Size    # rectangle dimensions

    class p 'Pos'
        : x: float
        : y: float

    class size 'Size'
        : width: float
        : heigth: float
"""

import time
import math
from collections import deque


class SolverError(Exception):
    """
    Constraint solver exception raised when constraints solution cannot be
    found.
    """



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
                if __debug__:
                    print('Unsolved: %s' % unsolved)
                raise SolverError('Could not find a solution;' \
                    ' unsolved={0} after {1} iterations' \
                    .format(len(unsolved), self.count))

        assert len(unsolved) == 0

        # some stats follow
        t2 = time.time()
        k = len(self._constraints)
        fmt = 'k=constraints: {k}, steps: {c}, O(k log k)={O}, time: {t:.3f}'
        if __debug__:
            print(fmt.format(k=k, c=self.count, O=int(math.log(k, 2) * k), t=t2 -t1))



class Constraint(object):
    """
    Basic class for all constraints.

    A constraint is a callable. When called it finds solution and returns
    list of variables, which changed due solution calculation.

    :Attributes:
     variables
        List of variables being manipulated by a constraint.
    """
    def __init__(self, *variables):
        super(Constraint, self).__init__()
        self.variables = list(variables)


    def __call__(self):
        """
        Find solution for constraint's variables and return changed
        variables.
        """
        raise NotImplemented('Constraint solution not implemented')



class MinSize(Constraint):
    """
    Rectangle minimal size constraint.
    """
    def __init__(self, r):
        super(MinSize, self).__init__(r)
        self.r = r


    def __call__(self):
        changed = []
        r = self.r
        w, h = r.min_size
        pad = r.padding
        if r.size.width < w:
            #r.ur.x = r.ll.x + w
            r.size.width += 10
            changed = [r]
        if r.size.height < h:
            #r.ur.y = r.ur.y + h
            r.size.height += 10
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
        super(RectConstraint, self).__init__(a, b)
        self.a = a
        self.b = b


class TopEq(RectConstraint):
    """
    Constraint to maintain top edges of two rectangles at the same
    position.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b
        if a.pos.y < b.pos.y:
            a.pos.y = b.pos.y
            changed = [a]
        if a.pos.y > b.pos.y:
            b.pos.y = a.pos.y
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
        if a.pos.y + a.size.height < b.pos.y + b.size.height:
            a.pos.y = b.pos.y + b.size.height - a.size.height
            changed = [a]
        if a.pos.y + a.size.height > b.pos.y + b.size.height:
            b.pos.y = a.pos.y + a.size.height - b.size.height
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
        if a.pos.x < b.pos.x:
            a.pos.x = b.pos.x
            changed = [a]
        if a.pos.x > b.pos.x:
            b.pos.x = a.pos.x
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
        if a.pos.x + a.size.width < b.pos.x + b.size.width:
            a.pos.x = b.pos.x + b.size.width - a.size.width
            changed = [a]
        if a.pos.x + a.size.width > b.pos.x + b.size.width:
            b.pos.x = a.pos.x + a.size.width - b.size.width
            changed = [b]
        return changed



class CenterEq(RectConstraint):
    """
    Constraint to center two rectangles horizontally.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b

        wa = a.size.width / 2.0
        wb = b.size.width / 2.0

        # calculate centres of both rectangles
        v1 = a.pos.x + wa
        v2 = b.pos.x + wb

        # move the middle of one of the rectangles
        if v1 > v2:
            b.pos.x = v1 - wb
            b.size.width = v1 + wb - b.pos.x
            changed = [b]
        elif v2 > v1:
            a.pos.x = v2 - wa
            a.size.width = v2 + wa - a.pos.x
            changed = [a]

        return changed



class MiddleEq(RectConstraint):
    """
    Constraint to center two rectangles vertically.
    """
    def __call__(self):
        changed = []
        a = self.a
        b = self.b

        ha = a.size.height / 2.0
        hb = b.size.height / 2.0

        # calculate centres of both rectangles
        v1 = a.pos.y + ha
        v2 = b.pos.y + hb

        # move the middle of one of the rectangles
        if v1 > v2:
            b.pos.y = v1 - hb
            b.size.height = v1 + hb - b.pos.y
            changed = [b]
        elif v2 > v1:
            a.pos.y = v2 - ha
            a.size.height = v2 + ha - a.pos.y
            changed = [a]

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
        if a.pos.x + a.size.width + self.dist > b.pos.x:
            b.pos.x = a.pos.x + a.size.width + self.dist
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
        if a.pos.y + a.size.height + self.dist > b.pos.y:
            b.pos.y = a.pos.y + a.size.height + self.dist
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
        super(Within, self).__init__(kid, parent)
        self.parent = parent
        self.kid = kid
        self.pad = pad


    def __call__(self):
        changed = set()
        p = self.parent
        k = self.kid
        pad = self.pad
        if p.pos.x + pad.left > k.pos.x:
            k.pos.x = p.pos.x + pad.left
            changed.add(k)
        if k.pos.x + k.size.width + pad.right > p.pos.x + p.size.width:
            p.size.width = k.pos.x + k.size.width + pad.right - p.pos.x
            changed.add(p)
        if p.pos.y + pad.top > k.pos.y:
            k.pos.y = p.pos.y + pad.top
            changed.add(k)
        if k.pos.y + k.size.height + pad.bottom > p.pos.y + p.size.height:
            p.size.height = k.pos.y + k.size.height + pad.bottom - p.pos.y
            changed.add(p)
        return changed



class Between(Constraint):
    """
    Keep a rectangle between other rectangles.

    :Attributes:
     a
        Rectangle to be aligned.
     others
        Alignment rectangles.
    """
    def __init__(self, a, others):
        super(Between, self).__init__(a, *others)
        self.a = a
        self.others = others


    def __call__(self):
        rects = sorted(self.others,
            cmp=lambda a, b: cmp(a.pos.x + a.size.width, b.pos.x))
        minx = rects[0]
        maxx = rects[-1]

        rects = sorted(self.others,
            cmp=lambda a, b: cmp(a.pos.y + a.size.height, b.pos.y))
        miny = rects[0]
        maxy = rects[-1]

        x = (minx.pos.x + minx.size.width + maxx.pos.x) / 2.0
        y = (miny.pos.y + miny.size.height + maxy.pos.y) / 2.0

        self.a.pos.x = x - self.a.size.width / 2.0
        self.a.pos.y = y - self.a.size.height / 2.0
        return []


# vim: sw=4:et:ai
