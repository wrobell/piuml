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

from spark import GenericASTTraversal
import gv

from piuml.data import Pos, Size, Edge
from piuml.parser import unwind


class GVGraph(GenericASTTraversal):
    """
    Generate Graphviz graph structure.

    Graph information is injected into Node.data['gv'].
    """
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self.g = None
        self.vertical = False
        self.size = Size(0, 0)


    def _get_pos(self, n):
        assert 'gv' in n.data
        gn = n.data['gv']
        w, h = self._get_size(n)
        dw, dh = self.size
        if n.is_packaging():
            x, y = map(float, gv.getv(gn, 'bb').split(','))[:2]
            y = dh - y - h
        else:
            x, y = map(float, gv.getv(gn, 'pos').split(','))
            x = x - w / 2.0
            y = dh - y - h / 2.0
        return Pos(x, y)


    def _get_size(self, n):
        assert 'gv' in n.data
        gn = n.data['gv']
        if n.is_packaging():
            x, y, w, h = map(float, gv.getv(gn, 'bb').split(','))
            return Size(w - x, h - y)
        else:
            return Size(float(gv.getv(gn, 'width')) * 72.0, float(gv.getv(gn, 'height')) * 72.0)


    def _get_edge(self, edge):
        # use edge's tail/head but if they are clusters, then use
        # first/last grouped node; fixme: in case of subclusters we need to
        # search deeper
        t = edge.tail[-1] if edge.tail.is_packaging() else edge.tail
        h = edge.head[0]  if edge.head.is_packaging() else edge.head

        gt = t.data['gv']
        gh = h.data['gv']
        e = gv.edge(gt, gh)

        gv.setv(e, 'arrowtail', 'none')
        gv.setv(e, 'arrowhead', 'none')

        # set cluster connection data for tail
        if edge.tail.is_packaging():
            t = edge.tail
            gv.setv(e, 'ltail', gv.getv(t.data['gv'], 'id'))

        # set cluster connection data for head
        if edge.head.is_packaging():
            h = edge.head
            gv.setv(e, 'lhead', gv.getv(h.data['gv'], 'id'))

        return e 


    def _to_gv(self, ast):
        for n in unwind(ast):
            if n.type == 'feature':
                continue

            gn = n.data['gv']
            if isinstance(n, Edge): # edges
                # use len attribute...
                gv.setv(gn, 'len', str(n.style.size.width / 72.0))
                # ... and minlen as well, which is rank difference - divide
                # by 30 to normalize to rank difference
                gv.setv(gn, 'minlen', str(n.style.size.width / 30.0))

            elif n.is_packaging(): # clusters
                w, h = n.style.size
                bottom = n.style.padding.bottom
                # a hack for cluster label and node alignment
                gv.setv(gn, 'fontsize', str((h - bottom)))
                # hack to set min width of cluster
                k = max(len(''.join(n.stereotypes)), len(n.name))
                gv.setv(gn, 'label', int(k / 2.5) * 'm')

            else: # clusters
                w, h = (str(p / 72.0) for p in n.style.size)
                gv.setv(gn, 'width', w)
                gv.setv(gn, 'height', h)


    def _from_gv(self, ast):
        dw, dh = self.size = ast.style.size = self._get_size(ast)

        for n in unwind(ast):
            if n.type == 'feature':
                continue
            if isinstance(n, Edge):
                gn = n.data['gv']
                p = gv.getv(gn, 'pos').split()
                n.style.edges = tuple(Pos(float(t.split(',')[0]), dh - float(t.split(',')[1])) for t in p)
            else:
                n.style.pos = self._get_pos(n)
                n.style.size = self._get_size(n)


    def create(self, ast):
        self.preorder(ast)


    def layout(self, ast):
        self._to_gv(ast)
        gv.layout(self.g, 'dot')
        gv.render(self.g, 'xdot', None)
        self._from_gv(ast)


    def n_diagram(self, n):
        self.g = g = gv.digraph('G')
        gv.setv(g, 'compound', 'true')
        gv.setv(g, 'clusterrank', 'local')
        gv.setv(g, 'splines', 'false')
        gv.setv(g, 'nodesep', str(50 / 72.0))
        if self.vertical:
            gv.setv(g, 'rankdir', 'TB')
        else:
            gv.setv(g, 'rankdir', 'LR')
        n.data['gv'] = g


    def n_element(self, n):
        """
        Generate UML element.
        """
        global filename, lineno
        g = self.g

        if n.parent.type == 'element':
            g = n.parent.data['gv']

        if n.is_packaging():
            id = 'cluster_' + n.id
            gn = gv.graph(g, id)
            if self.vertical:
                gv.setv(gn, 'labelloc', 'b')
        elif n.type != 'feature':
            id = n.id
            gn = gv.node(g, id)
            gv.setv(gn, 'fixedsize', 'true')
        gv.setv(gn, 'id', id)
        gv.setv(gn, 'shape', 'box')
        n.data['gv'] = gn


    def n_ielement(self, n):
        g = self.g

        id = n.id
        gn = gv.node(g, id)

        gv.setv(gn, 'id', id)
        gv.setv(gn, 'shape', 'box')
        gv.setv(gn, 'fixedsize', 'true')
        n.data['gv'] = gn


    def n_dependency(self, n):
        e = self._get_edge(n)
        n.data['gv'] = e


    n_commentline = n_connector = n_generalization = n_association \
        = n_dependency


# vim: sw=4:et:ai
