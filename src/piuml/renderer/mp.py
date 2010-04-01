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
MetaUML/Metapost based renderer.
"""

from spark import GenericASTTraversal
from piuml.data import ELEMENTS
from piuml.renderer.util import st_fmt


PATH_FMT = '%s.c -- %s.c cutbefore bpath(%s) cutafter bpath(%s)'

def _ids(nodes, f=lambda n: True):
    return (n.id for n in nodes if f(n))


class MRenderer(GenericASTTraversal):
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self._lines = []
        self.output = None
        self.filetype = 'pdf'

    def _add(self, data):
        self._lines.append(data)

    def dims(self, ast): pass

    def render(self, ast):
        self.preorder(ast)


    def n_diagram(self, node):
        self._add("""
input TEX;
input metauml;

% create bounding box path
vardef bpath(text box) =
    box.nw -- box.ne -- box.se -- box.sw -- cycle
enddef;

beginfig(1);
""");


    def n_diagram_exit(self, node):
        for c in node.constraints:
            self._add(c)
        ids = _ids(node, lambda n: n.type == 'element')
        self._add('drawObjects(%s);' % ', '.join(ids))

        for edge in node.unwind():
            if edge.type in ('dependency', 'generalization'):
                t, h = edge.head.id, edge.tail.id
                if edge.data['supplier'] is edge.head:
                    h, t = t, h
                ends = (t, h) * 2

                st = edge.stereotypes[:]
                lt = 'dependency'
                if edge.type == 'generalization':
                    lt = 'inheritance'
                elif 'realization' in st:
                    lt = 'realization'
                    st.remove('realization')
                    
                fmt = 'link(%s)(' + PATH_FMT + ');'
                self._add(fmt % ((lt,) + ends))
                if st:
                    self._add('label.rt("%s", 0.5[%s.c,%s.c]);' % (st_fmt(st), t, h));

        self._add("""
endfig;
end
""");
        f = open(self.output + '.mp', 'w')
        for l in self._lines:
            f.write(l)
            f.write('\n')
        f.close()

    def n_element(self, node):
        formats = dict(((e, e.capitalize() + '.{0}("{1}")()()') for e in ELEMENTS))
        formats['artifact'] = formats['class']
        if node.element == 'component':
            formats['component'] = formats['component'][:-3] \
                + ','.join(_ids(node, lambda n: n.type == 'element')) + ')'
        self._add(formats[node.element].format(node.id, node.name) + ';')

    def n_ielement(self, node):
        pass


# vim: sw=4:et:ai
