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
MetaUML/Metapost based layout.
"""

from piuml.layout import PreLayout

class MLayout(PreLayout):
    def size(self, node):
        ns = node.style

    def within(self, parent, node):
        ns = node.style
        ps = parent.style

    def top(self, *nodes):
        self._c('same.top(%s);' % ', '.join(n.id for n in nodes))

    def bottom(self, *nodes):
        self._c('same.bottom(%s);' % ', '.join(n.id for n in nodes))

    def left(self, *nodes):
        self._c('same.left(%s);' % ', '.join(n.id for n in nodes))

    def right(self, *nodes):
        self._c('same.right(%s);' % ', '.join(n.id for n in nodes))

    def center(self, *nodes):
        self._c('same.midx(%s);' % ', '.join(n.id for n in nodes))

    def middle(self, *nodes):
        self._c('same.midy(%s);' % ', '.join(n.id for n in nodes))

    def hspan(self, *nodes):
        nodes = list(nodes)
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            r = k1.style.margin.right
            l = k2.style.margin.left
            self._c('%s.right + %s = - %s + %s.left;' % (k1.id, r, l, k2.id))

    def vspan(self, *nodes):
        nodes = list(nodes)
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            b = k1.style.margin.bottom
            t = k2.style.margin.top
            self._c('%s.bottom - %s = %s + %s.top;' % (k1.id, b, t, k2.id))

# vim: sw=4:et:ai

