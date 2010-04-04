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

def id2mp(id):
    id = id.replace('a', 'aa').replace('1', 'a')
    id = id.replace('b', 'bb').replace('2', 'b')
    return id

def _ids(nodes, f=lambda n: True):
    return (n.id for n in nodes if f(n))


class MRenderer(GenericASTTraversal):
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self._defs = []
        self._draws = []
        self.output = None
        self.filetype = 'pdf'

    def _def(self, data):
        self._defs.append(data)

    def _draw(self, data):
        self._draws.append(data)

    def dims(self, ast): pass

    def render(self, ast):
        self.preorder(ast)


    def n_diagram(self, node):
        self._def("""
input boxes;

prologues:=3;

vardef size(expr t) =
    save tempPic;
    picture tempPic;
    tempPic := image(draw t);
    urcorner tempPic
enddef;

beginfig(1);

% boxes padding is calculated by us
defaultdx:=0;
defaultdy:=0;

""");


    def n_diagram_exit(self, node):
        for c in node.constraints:
            self._def(c)
        self._draw("""
endfig;
end
""");

        #f = open(self.output + '.mp', 'w')
        f = open('cl.mp', 'w')
        for l in self._defs + self._draws:
            f.write(l)
            f.write('\n')
        f.close()

    def _pre_border(self, node):
        id = id2mp(node.id)
        self._def("""
% UML {type}: "{name}"
boxit.{id}();
""".format(id=id, name=node.name, type=node.element))

    def _post_border(self, node, comp):
        id = id2mp(node.id)

        # calculate initial size of element
        self._def("""
{id}Width := max(xpart {id}NameSize, 80);
{id}Height := max(ypart {id}NameSize, 40);
""".format(id=id))

        # calculate size of each compartment
        # and position it within the element
        if len(comp) > 0:
            p = comp[0]
            self._def("""
% position of first compartment
xpart {id}Comp{cid}.nw = xpart {id}.w;
ypart {id}Comp{cid}.nw = ypart {id}Name.sw;

% increase total size of element
{id}Width := max({id}Width, xpart {id}CompSize{cid});
{id}Height := {id}Height + ypart {id}CompSize{cid};
    """.format(id=id, cid=p))

            for cid in comp[1:]:
                self._def("""
% increase total size of element
{id}Width := max({id}Width, xpart {id}CompSize{cid});
{id}Height := {id}Height + ypart {id}CompSize{cid};

% position of compartment
xpart {id}Comp{cid}.nw = xpart {id}Comp{pcid}.nw;
ypart {id}Comp{cid}.nw = ypart {id}Comp{pcid}.sw;
    """.format(id=id, pcid=p, cid=cid))
                p = cid

        # set size of the element
        self._def("""
{id}.se = {id}.nw + ({id}Width, -{id}Height);
""".format(id=id))

        # draw name
        self._draw("""
drawunboxed({id}Name);
""".format(id=id))

        # draw compartments
        for cid in comp:
            self._draw("""
drawunboxed({id}Comp{cid});
""".format(id=id, cid=cid))

        # draw element border
        self._draw("""
drawboxed({id});
""".format(id=id))

        # draw compartment separator
        for cid in comp:
            self._draw("""
draw (xpart {id}.w, ypart {id}Comp{cid}.n) -- (xpart {id}.e, ypart {id}Comp{cid}.n);
""".format(id=id, cid=cid))

    def _name(self, node):
        id = id2mp(node.id)
        style = node.style
        pad = style.padding
        name = '\\bf ' + node.name
        if node.stereotypes:
            st = st_fmt(node.stereotypes)
            name = '\\vbox{\\hbox{' + st + '}\\hbox{' + name + '}}'

        self._def("""
pair {id}NameSize;
{id}NameSize := size(btex {name} etex) + ({padw}, {padh});
boxit.{id}Name(btex {name} etex);
{id}Name.sw = {id}Name.ne - {id}NameSize;
{id}Name.n = {id}.n;
""".format(id=id, name=name, type=node.element,
        padw=pad.left + pad.right,
        padh=pad.top + pad.bottom))

    def _compartment(self, node, cid, comp, title=''):
        """
        :Parameters:
         cid
          Compartment id.
         comp
          List of compartment items.
        """
        id = id2mp(node.id)
        style = node.style
        pad = style.padding
        comp_s = '\\vbox{' \
                + ('\\hbox{%s}' % title if title else '') \
                + ''.join('\\hbox{%s}' % s for s in comp) \
                + '}'
        self._def("""
pair {id}CompSize{cid};
{id}CompSize{cid} := size(btex {comp} etex) + ({padw}, {padh});
boxit.{id}Comp{cid}(btex {comp} etex);
{id}Comp{cid}.sw = {id}Comp{cid}.ne - {id}CompSize{cid};
""".format(id=id, cid=cid, comp=comp_s,
        padw=pad.left + pad.right,
        padh=pad.top + pad.bottom))


    def n_element(self, node):
        attrs = [f.name for f in node if f.element == 'attribute']
        opers = [f.name for f in node if f.element == 'operation']
        st_attrs = [f for f in node if f.element == 'stattributes']
        cl = 0

        self._pre_border(node)
        self._name(node);
        if attrs:
            self._compartment(node, 'A', attrs)
            cl += 1
        if opers:
            self._compartment(node, 'B', opers)
            cl += 1
        import string
        ids = string.ascii_uppercase
        for cid, sta in zip(ids[cl:], st_attrs):
            attrs = [f.name for f in sta]
            self._compartment(node, cid, attrs, title=st_fmt([sta.name]))
            cl += 1
        self._post_border(node, ids[:cl])

        if node.element in ('package', 'profile'):
            self._draw("""
draw {id}.nw -- {id}.nw + (0, 20) -- {id}.nw + (50, 20) -- {id}.nw + (50, 0);
""".format(id=id2mp(node.id)))
        elif node.element in ('node', 'device'):
            self._draw("""
draw {id}.nw -- {id}.nw + (10, 10) -- {id}.ne + (10, 10) -- {id}.se + (10, 10) -- {id}.se;
draw {id}.ne --  {id}.ne + (10, 10);
""".format(id=id2mp(node.id)))

    def n_ielement(self, node):
        pass


# vim: sw=4:et:ai
