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

def id2mp(id):
    id = id.replace('a', 'aa').replace('1', 'a')
    id = id.replace('b', 'bb').replace('2', 'b')
    return id

from piuml.layout import PreLayout

class MLayout(PreLayout):
    def size(self, node):
        ns = node.style

    def within(self, parent, node):
        ns = node.style
        ps = parent.style

    def top(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('ypart %s.n = ypart %s.n;' % (id1, id2));

    def bottom(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('ypart %s.s = ypart %s.s;' % (id1, id2));

    def left(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('xpart %s.w = xpart %s.w;' % (id1, id2));

    def right(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('xpart %s.e = xpart %s.e;' % (id1, id2));

    def center(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('xpart %s.c = xpart %s.c;' % (id1, id2));

    def middle(self, *nodes):
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('ypart %s.c = ypart %s.c;' % (id1, id2));

    def hspan(self, *nodes):
        nodes = list(nodes)
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            w = k1.style.margin.right + k2.style.margin.left
            c = self.ast.data['edges'].get((k1.id, k2.id), 0)
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('xpart %s.w - xpart %s.e = %s;' % (id2, id1, max(w, c)))

    def vspan(self, *nodes):
        nodes = list(nodes)
        for k1, k2 in zip(nodes[:-1], nodes[1:]):
            w = k1.style.margin.bottom + k2.style.margin.top
            c = self.ast.data['edges'].get((k1.id, k2.id), 0)
            id1 = id2mp(k1.id)
            id2 = id2mp(k2.id)
            self._c('ypart %s.s - ypart %s.n = %s;' % (id1, id2, max(w, c)))

    def n_dependency(self, edge):
        t, h = edge.tail, edge.head
        self.ast.data['edges'][t.id, h.id] = 50
        self.ast.data['edges'][h.id, t.id] = 50

# vim: sw=4:et:ai

