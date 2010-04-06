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
from piuml.renderer.util import st_fmt as _st_fmt
from collections import namedtuple
import string

# compartment has an id, the title (i.e. stereotype) and data, which is
# compartment's content
Compartment = namedtuple('Compartment', 'id title data')

def st_fmt(stereotypes):
    s = _st_fmt(stereotypes)
    s = s.replace('<<', '$\\ll$')
    s = s.replace('>>', '$\\gg$')
    return s

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
    save ll, ur, p;
    pair ll, ur, wh;
    picture p;
    truecorners := 1;
    p := image(draw t);
    ll := llcorner p;
    ur := urcorner p;
    wh := (xpart ur - xpart ll, ypart ur - ypart ll);
    write id & "," & decimal xpart wh & "," & decimal ypart wh to "sizesT.csv";
enddef;
beginfig(1);
""")
            ccounts = {}
            for k in ast.unwind():
                if k.type != 'element':
                    continue

                fmt = 'size("{id},{type}")(btex {text} etex);\n'
                # calculate size of name...
                name = self._name_s(k)
                f.write(fmt.format(id=k.id, type='name', text=name))

                # ... and compartments
                comps = self._compartments(k)
                ctext = ''
                if comps:
                    ctext = ''
                    for c in comps:
                        ctext += '\\hbox{' + c.data + '}'
                    ctext = '\\vbox{' + ctext + '}'
                f.write(fmt.format(id=k.id, type='compartment', text=ctext))

                # how many times padding is used?
                ccounts[k.id] = 1 + len(comps)

            f.write('endfig;\nend')
        #cmd('mpost', '-interaction', 'batchmode', 'sizesT.mp', tmpdir='.')
        cmd('mptopdf', 'sizesT.mp', tmpdir='.')
        import csv

        f = csv.reader(open('sizesT.csv'))
        data = {}
        width, height = 0, 0
        for l in f:
            id = l[0]
            t = l[1]
            w, h = float(l[2]), float(l[3])

            if t == 'name':
                width, height = w, h

            elif t == 'compartment':
                style = ast.cache[id].style
                pad = style.padding
                default_w, default_h = style.size
                head = height

                # reset compartments size if there is none
                if ccounts[id] == 1:
                    w, h = 0, 0

                # include head size
                w += width + pad.left + pad.right
                h += height + ccounts[id] * (pad.top + pad.bottom)
                w, h = max(w, default_w), max(h, default_h)

                # define minimal sizes
                style.size = Size(w, h)
                style.head = head
            else:
                assert False

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

vardef drawArrow(text a)(text b)(expr closed) =
  numeric alfa;
  alfa = angle(xpart(a - b), ypart(a - b));

  pair w[];
  w[1] := (15, 6);
  w[1] := w[1] rotated (alfa) shifted b;
  w[2] := (-15, 6);
  w[2] := w[2] rotated (180 + alfa) shifted b;

  if closed:
      path p;
      p := w[1] -- b -- w[2] -- cycle;
      unfill p;
      draw p;
  else:
      draw w[1] -- b -- w[2];
  fi
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


    def _element(self, node, comps, border=True, underline=False, bold=True):
        """
        Draw name and compartments of an element.

        :Parameters:
         node
            Node of element to draw.
         comps
            List of compartments.
         border
            Draw border around element if true.
        """
        id = id2mp(node.id)
        style = node.style
        pad = style.padding

        name = self._name_s(node, underline, bold)
        # define the element's box and its name
        self._def("""
% UML {type}: "{nc}"
boxit.{id}();
{id}.sw = ({x}, {y});
{id}.ne = {id}.sw + ({w}, {h});
boxit.{id}Name(btex {name} etex);

        """.format(id=id, nc=node.name, type=node.element,
            name=name,
            x=float(style.ll.x), y=float(style.ll.y),
            w=style.size.width, h=style.size.height))

        if node.element == 'usecase':
            self._def('{id}Name.c = {id}.c;'.format(id=id))
        elif node.element == 'actor':
            self._def('{id}Name.n + (0, {pad.bottom}) = {id}.s;'.format(id=id, pad=pad))
        else:
            self._def('{id}Name.n + (0, {pad.top}) = {id}.n;'.format(id=id,
                pad=pad))

        # define compartments
        for c in comps:
            self._def('boxit.{id}Comp{cid}(btex {comp} etex);'.format(id=id,
                cid=c.id,
                comp=c.data))

        # calculate size of each compartment
        # position each compartment within the element
        # it is done from bottom to top
        if len(comps) > 0:
            p = comps[-1].id
            self._def("""
% position of last compartment
xpart {id}Comp{cid}.w = xpart {id}.w + {pad.left};
ypart {id}Comp{cid}.s = ypart {id}.s + {pad.bottom};
            """.format(id=id, cid=p, pad=pad))

            for c in reversed(comps[:-1]):
                self._def("""
% position of compartment {cid}
xpart {id}Comp{cid}.w = xpart {id}Comp{pcid}.w;
ypart {id}Comp{pcid}.n + {pad.top} = ypart {id}Comp{cid}.s - {pad.bottom};
                """.format(id=id, pcid=p, cid=c.id, pad=pad))

                p = c.id # note this assignment


        # draw name
        self._draw("""
drawunboxed({id}Name);
        """.format(id=id))

        # draw compartments in reversed order to solve metapost linear
        # equations properly
        for c in reversed(comps):
            self._draw("""
drawunboxed({id}Comp{cid});
            """.format(id=id, cid=c.id))

        # draw element border
        shape = 'drawboxed' if border else 'drawunboxed'
        self._draw("""
{shape}({id});
        """.format(id=id, shape=shape))

        # draw compartment separator
        for c in comps:
            self._draw("""
draw (xpart {id}.w, ypart {id}Comp{cid}.n + {pad.top})
    -- (xpart {id}.e, ypart {id}Comp{cid}.n + {pad.top});
        """.format(id=id, cid=c.id, pad=pad))


    def _name_s(self, node, underline=False, bold=True):
        name = node.name
        if bold:
            name = '\\bf ' + name
        if underline:
            name = '\\underbar{' + name + '}'
        if node.stereotypes:
            fmt = '\\vbox{\\halign{\\hfil \\quad # \\hfil \\cr %s \\cr %s \\cr}}'
            st = st_fmt(node.stereotypes)
            name = fmt % (st, name)
        return name


    def _comp_s(self, comp, title=''):
        return '\\vbox{' \
                + ('\\hbox{%s}' % title if title else '') \
                + ''.join('\\hbox{%s}' % s for s in comp) \
                + '}'


    def _compartments(self, node):
        """
        Create list of compartments for specified element.

        :Parameters:
         node
            Element's node.
        """
        attrs = [f.name for f in node if f.element == 'attribute']
        opers = [f.name for f in node if f.element == 'operation']
        st_attrs = [f for f in node if f.element == 'stattributes']

        cids = (c for c in string.uppercase)
        data = []
        if attrs:
            data.append(Compartment(cids.next(), '', self._comp_s(attrs)))
        if opers:
            data.append(Compartment(cids.next(), '', self._comp_s(opers)))
        for sta in st_attrs:
            attrs = [f.name for f in sta]
            title = st_fmt([sta.name])
            c = Compartment(cids.next(), title, self._comp_s(attrs, title=title))
            data.append(c)
        return data


    def n_element(self, node):
        id = id2mp(node.id)
        underline = node.element == 'instance'
        border = node.element not in ('usecase', 'actor', 'comment')
        bold = node.element != 'comment'
        style = node.style
        pad = style.padding
        ipad = 5
        icon_w = style.icon_size.width
        icon_h = style.icon_size.height

        # compartments
        comps = self._compartments(node)

        # draw element and its compartments
        self._element(node, comps, border=border, underline=underline, bold=bold)

        # custom shapes
        if node.element in ('package', 'profile'):
            self._draw("""
draw {id}.nw -- {id}.nw + (0, 20) -- {id}.nw + (50, 20) -- {id}.nw + (50, 0);
""".format(id=id))

        elif node.element in ('node', 'device'):
            self._draw("""
draw {id}.nw -- {id}.nw + (10, 10) -- {id}.ne + (10, 10) -- {id}.se + (10, 10) -- {id}.se;
draw {id}.ne --  {id}.ne + (10, 10);
""".format(id=id))

        # icons
        if node.element == 'component':
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
            p = '{id}.ne - ({ipad}, {ipad})'.format(id=id, ipad=ipad)
            self._draw("""
draw {p} - ({w}, 0) -- {p} - (5, 0)-- {p} - (0, 5)
    -- {p} - (0, {h}) -- {p} - ({w}, {h}) -- cycle;
draw {p} - (5, 0) -- {p} - (5, 5) -- {p} - (0, 5);
""".format(p=p, w=icon_w, h=icon_h))
        elif node.element == 'usecase':
            self._draw("""
draw fullcircle
    xscaled (xpart {id}.w - xpart {id}.e)
    yscaled (ypart {id}.s - ypart {id}.n) shifted {id}.c;
""".format(id=id));
        elif node.element == 'actor':
            self._draw("""
% head
draw {id}.n .. {id}.n + (10, -10) .. {id}.n + (0, -20)
    .. {id}.n + (-10, -10) ..  cycle;
% body
draw {id}.n + (0, -20) -- {id}.n + (0, -40);
% arms
draw {id}.n + (-20, -35) -- {id}.n + (0, -25) -- {id}.n + (20, -35);
% legs
draw {id}.n + (-20, -60) -- {id}.n + (0, -40) -- {id}.n + (20, -60);
            """.format(id=id));

        elif node.element == 'comment':
            self._draw("""
draw {id}.nw -- {id}.ne - (15, 0) -- {id}.ne - (0, 15)
    -- {id}.se -- {id}.sw -- cycle;
draw {id}.ne - (15, 0) -- {id}.ne - (15, 15) -- {id}.ne - (0, 15);
            """.format(id=id))


    def n_ielement(self, node):
        pass


    def n_dependency(self, node):
        t = id2mp(node.tail.id)
        h = id2mp(node.head.id)
        dashed = node.element != 'generalization'
        closed = node.element == 'generalization' 

        st = ''
        if node.stereotypes:
            stl = node.stereotypes[:]
            if 'realization' in node.stereotypes:
                stl.remove('realization')
                closed = True
            st = st_fmt(stl)

        p1 = 'point 0 of tempPath'
        p2 = 'point length tempPath of tempPath'
        if node.tail is node.data['supplier']:
            p2, p1 = p1, p2
        arrow = '(' + p1 + ')(' + p2 + ')'
        path = """
path tempPath;
tempPath := {t}.c -- {h}.c cutbefore bpath {t} cutafter bpath {h};
"""
        path += 'draw tempPath'
        if dashed:
            path += ' dashed evenly scaled 1.2'
        path += ';\n'

        closed = 'true' if closed else 'false'
        self._draw((path + 'drawArrow{arrow}({closed});').format(t=t, h=h,
            arrow=arrow, closed=closed))

        if st:
            self._draw('label.top(btex {st} etex, 0.5[{p1},{p2}]);'.format(st=st, p1=p1, p2=p2))

    n_generalization = n_dependency


    def n_commentline(self, line):
        """
        Draw comment line.
        """
        t = id2mp(line.tail.id)
        h = id2mp(line.head.id)
        self._draw("""
draw {t}.c -- {h}.c cutbefore bpath {t} cutafter bpath {h}
    dashed evenly scaled 1.2;
        """.format(t=t, h=h))


# vim: sw=4:et:ai
