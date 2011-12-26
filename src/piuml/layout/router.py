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

ARouter library is used for line routing.
"""

from piuml.style import Pos
from piuml.data import unwind, Element, Relationship

import arouter

class Router(object):
    """
    Line router implementation using ARouter.
    """

    def route(self, ast):
        """
        Route all lines defined in piUML diagram.

        :Parameters:
         ast
            Diagram start node.
        """
        ncache = {}
        lcache = {}

        router = arouter.Router()

        nodes = (n for n in unwind(ast)
                if isinstance(n, Element)
                    and not isinstance(n, Relationship))
        for n in nodes:
            x, y = n.style.pos
            w, h = n.style.size
            shape = (x, y), (x + w, y + h)
            s = router.add(shape)
            ncache[n.id] = s

        lines = (l for l in ast if isinstance(l, Relationship))
        for l in lines:
            h = ncache[l.head.id]
            t = ncache[l.tail.id]
            c = router.connect(h, t)
            lcache[l] = c

        router.route()

        for l, c in list(lcache.items()):
            l.style.edges = tuple(Pos(*p) for p in reversed(router.edges(c)))


# vim: sw=4:et:ai
