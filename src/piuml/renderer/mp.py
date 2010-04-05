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
from piuml.data import ELEMENTS, Size
from piuml.renderer.util import st_fmt


##
## cmd
##
import subprocess
import os
import os.path
import shutil


class CmdError(RuntimeError):
    def __init__(self, output):
        self.output = output

def cmd(*args, **kw):
    tmpdir = kw.get('tmpdir', '.')
    p = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=tmpdir)
    out, err = p.communicate()
    if p.returncode != 0:
        raise CmdError(out + '\n' + err)
    return p.returncode


def save(fnout, data):
    fn = 'aa.mp'
    fbase, _ = os.path.splitext(fn)
    fnout = fbase + '.pdf'
    tmpdir = os.tempnam('.', 'piuml')
    tmpdir = 'tmp'
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)

    f = open(tmpdir + '/' + fn, 'w')
    for l in data:
        f.write(l)
    f.close()

    try:
        cmd('mpost', '-interaction', 'batchmode', fn, tmpdir=tmpdir)
        cmd('epstopdf', tmpdir + '/' + fbase + '.1', '-o', fnout)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

##
## end of cmd
##






def id2mp(id):
    id = id.replace('a', 'aa').replace('1', 'a')
    id = id.replace('b', 'bb').replace('2', 'b')
    id = id.replace('c', 'cc').replace('3', 'c')
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

    def constraint(self, ast):
        with open('sizesT.mp', 'w') as f:
            f.write("""
vardef size(text id)(expr t) =
    save wh;
    pair wh;
    wh := urcorner image(draw t);
    write id & "," & decimal xpart wh & "," & decimal ypart wh to "sizesT.csv";
enddef;
beginfig(1);
""")
            pad_counts = {}
            for k in ast.unwind():
                if k.type != 'element':
                    continue
                text = self._name_s(k)
                data = self._compartments_s(k)
                if data:
                    text = '\\hbox{' + text + '}'
                    for d in data:
                        text += '\\hbox{' + d + '}'
                    text = '\\vbox{' + text + '}'
                pad_counts[k.id] = 1 + len(data)
                f.write('size("{id}")(btex {text} etex);\n'.format(id=k.id,
                    text=text))

            f.write('endfig;\nend')
        cmd('mpost', '-interaction', 'batchmode', 'sizesT.mp', tmpdir='.')
        import csv

        f = csv.reader(open('sizesT.csv'))
        data = {}
        for l in f:
            id = l[0]
            w1, h1 = float(l[1]), float(l[2])

            style = ast.cache[id].style
            pad = style.padding
            w2, h2 = style.size
            dh = pad_counts[id] * pad.top + pad.bottom

            print id, w1, h1, w2, h2
            style.size = Size(max(w1 + pad.left + pad.right, w2), max(h1 + dh, h2))
#try:
#    save('aa.pdf', data)
#except CmdError, e:
#    print e.output

            

    def render(self, ast):
        self.preorder(ast)


    def n_diagram(self, node):
        self._def("""
input boxes;

prologues:=3;

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
        style = node.style
        self._def("""
% UML {type}: "{name}"
boxit.{id}();
{id}.ne = ({x}, {y});
{id}.ne = {id}.sw + ({w}, {h});
""".format(id=id, name=node.name, type=node.element,
    x=float(style.pos.x), y=float(style.pos.y),
    w=style.size.width, h=style.size.height))

    def _post_border(self, node, comp):
        id = id2mp(node.id)
        style = node.style
        pad = style.padding

        self._def("""
{id}Name.n = {id}.n - (0, {pad.top});
""".format(id=id, pad=pad))

        # calculate size of each compartment
        # and position it within the element
        if len(comp) > 0:
            p = comp[0]
            self._def("""
% position of first compartment
xpart {id}Comp{cid}.w = xpart {id}.w + {pad.left};
ypart {id}Comp{cid}.n = ypart {id}Name.s - ({pad.bottom} + {pad.top});
    """.format(id=id, cid=p, pad=pad))

            for cid in comp[1:]:
                self._def("""
% position of compartment
xpart {id}Comp{cid}.w = xpart {id}Comp{pcid}.w;
ypart {id}Comp{cid}.n = ypart {id}Comp{pcid}.s - ({pad.bottom} + {pad.top});
    """.format(id=id, pcid=p, cid=cid, pad=pad))
                p = cid

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
draw (xpart {id}.w, ypart {id}Comp{cid}.n + {pad.top})
    -- (xpart {id}.e, ypart {id}Comp{cid}.n + {pad.top});
""".format(id=id, cid=cid, pad=pad))


    def _name_s(self, node, underline=False):
        name = '\\bf ' + node.name
        if underline:
            name = '\\underbar{' + name + '}'
        if node.stereotypes:
            st = st_fmt(node.stereotypes)
            name = '\\hbox{ ' + st + '}\\hbox{' + name + '}'
        return name



    def _name(self, node, underline=False):
        id = id2mp(node.id)
        name = self._name_s(node, underline)
        self._def('boxit.{id}Name(btex {name} etex);'.format(id=id, name=name))


    def _comp_s(self, comp, title=''):
        return '\\vbox{' \
                + ('\\hbox{%s}' % title if title else '') \
                + ''.join('\\hbox{%s}' % s for s in comp) \
                + '}'


    def _compartments_s(self, node):
        attrs = [f.name for f in node if f.element == 'attribute']
        opers = [f.name for f in node if f.element == 'operation']
        st_attrs = [f for f in node if f.element == 'stattributes']

        data = []
        if attrs:
            data.append(self._comp_s(attrs))
        if opers:
            data.append(self._comp_s(opers))
        for sta in st_attrs:
            attrs = [f.name for f in sta]
            data.append(self._comp_s(attrs, title=st_fmt([sta.name])))
        return data


    def _compartment(self, node, cid, comp):
        """
        :Parameters:
         cid
          Compartment id.
         comp
          Compartment string.
        """
        id = id2mp(node.id)
        style = node.style
        pad = style.padding
        self._def('boxit.{id}Comp{cid}(btex {comp} etex);'.format(id=id,
            cid=cid,
            comp=comp))


    def _area(self, node):
        """
        Packaged elements.
        """


    def n_element(self, node):
        underline = node.element == 'instance'
        boxshape = node.element not in ('usecase',)
        style = node.style
        pad = style.padding
        ipad = 5
        icon_w = style.icon_size.width
        icon_h = style.icon_size.height

        self._pre_border(node)
        self._name(node, underline=underline);
#
#       # packaging area
#       self._area(node)
#
        import string
        data = self._compartments_s(node)
        ids = string.ascii_uppercase[:len(data)]
        for cid, comp in zip(ids, data):
            self._compartment(node, cid, comp)
        self._post_border(node, ids)

        # custom shapes
        if node.element in ('package', 'profile'):
            self._draw("""
draw {id}.nw -- {id}.nw + (0, 20) -- {id}.nw + (50, 20) -- {id}.nw + (50, 0);
""".format(id=id2mp(node.id)))

        elif node.element in ('node', 'device'):
            self._draw("""
draw {id}.nw -- {id}.nw + (10, 10) -- {id}.ne + (10, 10) -- {id}.se + (10, 10) -- {id}.se;
draw {id}.ne --  {id}.ne + (10, 10);
""".format(id=id2mp(node.id)))

        # icons
        if node.element == 'component':
            id = id2mp(node.id)
            p = '{id}.ne - ({ipad}, {ipad})'.format(id=id, ipad=ipad)
            self._draw("""
draw {p} - ({w}, {h} / 5) 
    -- {p} - ({w}, 0) -- {p} -- {p} - (0, {h}) -- {p} - ({w}, {h})
    -- {p} - ({w}, 4 * {h} / 5);
draw {p} - ({w}, 3 * {h} / 5) -- {p} - ({w}, 2 * {h} / 5);
% bars
draw {p} - ({w} + {w} / 3, {h} / 5) -- {p} - ({w} - {w} / 3, {h} / 5)
    -- {p} - ({w} - {w} / 3, 2 * {h} / 5) -- {p} - ({w} + {w} / 3, 2 * {h} / 5)
    -- cycle;
draw {p} - ({w} + {w} / 3, 3 * {h} / 5) -- {p} - ({w} - {w} / 3, 3 * {h} / 5)
    -- {p} - ({w} - {w} / 3, 4 * {h} / 5) -- {p} - ({w} + {w} / 3, 4 * {h} / 5)
    -- cycle;
""".format(p=p, w=icon_w, h=icon_h))

        elif node.element == 'artifact':
            id = id2mp(node.id)
            p = '{id}.ne - ({ipad}, {ipad})'.format(id=id, ipad=ipad)
            self._draw("""
draw {p} - ({w}, 0) -- {p} - (5, 0)-- {p} - (0, 5)
    -- {p} - (0, {h}) -- {p} - ({w}, {h}) -- cycle;
draw {p} - (5, 0) -- {p} - (5, 5) -- {p} - (0, 5);
""".format(p=p, w=icon_w, h=icon_h))

    def n_ielement(self, node):
        pass


# vim: sw=4:et:ai
