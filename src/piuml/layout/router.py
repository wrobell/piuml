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

"""
Line router for piUML diagrams.
"""

import operator
from collections import namedtuple

from piuml.data import Pos, lsb


# obstacle consists of a line, which is part of a graphical representation
# of piuml language node; line is a tuple and consists of two positions
Obstacle = namedtuple('Obstacle', 'node line')


class Router(object):
    """
    Line router algorithm implementation.

    The algorithm finds line path by omitting obstacles. The line path
    should have minimal amount of segments.

    Algorithm steps are as follows

    - pickup nodes, which are obstacles for line path to be routed
    - extract shapes of obstacles (vertical and horizontal lines)
    - sort obstacles vertically
    - sort obstacles horizontally
    - find way around vertical boundaries
    - find way around horizontal boundaries

    Method Router.route finds line paths for all piUML diagram lines.
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
            nodes = self._pickup(ast, t, h)
            vo, ho = self._shapes(nodes)
            vs = self._sort(vo, vert=True)
            hs = self._sort(ho, vert=False)

            #borders = self._swipe(t, h, vs)

            def shortest(t, h):
                r = sorted(self._bbox(t) + self._bbox(h), key=operator.attrgetter('x'))
                return r[len(r) / 2 - 1], r[len(r) / 2]

            line.style.edges = shortest(t, h)


    def _pickup(self, ast, start, end):
        """
        Pick up nodes, which are obstacles for line routing.

        Start and end nodes are not obstacles, therefore not contained in
        the result.

        List of node-obstacles is returned.

        :Parameters:
         ast
            Diagram root node.
         start
            Line start node.
         end
            Line end node.
        """
        # get parents of start/end nodes
        pse = lsb(ast, start, end)

        # get the nodes being obstacles for line to be routed between start
        # and end nodes
        nodes = [n for n in ast if n not in pse]

        if start.parent is not ast:
            nodes.extend(n for n in start.parent if n is not start)
        if end.parent is not ast:
            nodes.extend(n for n in end.parent if n is not end)

        assert start not in nodes and end not in nodes, '%s' % nodes

        return nodes


    def _shapes(self, nodes):
        """
        Extract obstacle shapes from nodes.

        Two lists of obstacles are returned - vertical and horizontal lines
        creating boundary for each processed node.

        :Parameters:
         nodes
            List of nodes-obstacles.

        :seealso:
            Obstacle
        """
        vo = []
        ho = []
        for n in nodes:
            x, y = n.style.pos
            w, h = n.style.size

            vo.append(Obstacle(n, (Pos(x, y), Pos(x, y + h))))
            vo.append(Obstacle(n, (Pos(x + w, y), Pos(x + w, y + h))))

            ho.append(Obstacle(n, (Pos(x, y), Pos(x + w, y))))
            ho.append(Obstacle(n, (Pos(x, y + h), Pos(x + w, y + h))))

        assert len(vo) == len(ho) == 2 * len(nodes)

        return vo, ho


    def _sort(self, obstacles, vert=True):
        """
        Sort obstacles in vertical or horizontal way.

        :Parameters:
         obstacles
            List of obstacles to sort.
         vert
            Sort vertically if set to true.
        """
        if vert:
            f = lambda n: n.line[0].x
        else:
            f = lambda n: n.line[0].y

        return sorted(obstacles, key=f)


    #def _swipe(start, end, 



    def _bbox(node):
        x1, y1 = node.style.pos
        w, h = node.style.size
        x2 = x1 + w
        y2 = y1 + h
        x = (x1 + x2) / 2.0
        y = (y1 + y2) / 2.0
        return Pos(x1, y), Pos(x2, y), Pos(x, y1), Pos(x, y2)


# vim: sw=4:et:ai
