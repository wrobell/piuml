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
            w = k1.style.margin.right + k2.style.margin.left
            c = self.ast.data['edges'].get((k1.id, k2.id), 0)
            self._c('%s.left - %s.right = %s;' % (k1.id, k2.id, max(w, c)))

    def vspan(self, *nodes):
        nodes = list(nodes)
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            w = k1.style.margin.bottom + k2.style.margin.top
            c = self.ast.data['edges'].get((k1.id, k2.id), 0)
            self._c('%s.bottom - %s.top = %s;' % (k1.id, k2.id, max(w, c)))

    def n_dependency(self, edge):
        t, h = edge.tail, edge.head
        self.ast.data['edges'][t.id, h.id] = 50
        self.ast.data['edges'][h.id, t.id] = 50

# vim: sw=4:et:ai

