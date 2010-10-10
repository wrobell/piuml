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

import operator

from piuml.data import Pos

class Router(object):
    """
    Line router for piUML diagrams.
    """

    def route(self, ast):
        """
        Route all lines defined in piUML diagram.

        :Parameters:
         ast
            Diagram start node.
        """
        lines = (l for l in ast if l.type == 'line')
        for line in lines:
            t, h = line.tail, line.head
            def get_cp(node):
                x1, y1 = node.style.pos
                w, h = node.style.size
                x2 = x1 + w
                y2 = y1 + h
                x = (x1 + x2) / 2.0
                y = (y1 + y2) / 2.0
                return Pos(x1, y), Pos(x2, y), Pos(x, y1), Pos(x, y2)

            def shortest(t, h):
                r = sorted(get_cp(t) + get_cp(h), key=operator.attrgetter('x'))
                return r[len(r) / 2 - 1], r[len(r) / 2]

            line.style.edges = shortest(t, h)


# vim: sw=4:et:ai
