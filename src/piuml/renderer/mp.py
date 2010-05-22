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
MetaPost based renderer.
"""

from spark import GenericASTTraversal

from collections import namedtuple
import csv
import string
import os
import os.path
import shutil

from piuml.cmd import cmd
from piuml.data import ELEMENTS, Size
from piuml.renderer.util import st_fmt as _st_fmt


# compartment has an id, the title (i.e. stereotype) and data, which is
# compartment's content
Compartment = namedtuple('Compartment', 'id title data')

def st_fmt(stereotypes):
    s = _st_fmt(stereotypes)
    s = s.replace('<<', '$\\ll$')
    s = s.replace('>>', '$\\gg$')
    return s


def id2mp(id):
    """
    Convert and id to MetaPost token.
    """
    id = id.replace('H', 'HH').replace('-', 'H')
    id = id.replace('dir', 'dirdir') # dir is mp keyword

    for l, d in zip(string.uppercase, string.digits):
        id = id.replace(l, l + l).replace(d, l)
    return id


def qstr(text):
    """
    Quote string to render it with TeX.
    """
    t = ['\\hbox{%s}' % s for s in text.split('\\n')]
    if len(t) > 1:
        return '\\vbox{' + ''.join(t) + '}'
    else:
        return t[0]


def _ids(nodes, f=lambda n: True):
    return (n.id for n in nodes if f(n))


def save(fout, data):
    """
    Process MetaPost program and save it to specified file.

    :Parameters:
     fout
        Target file name.
     data
        MetaPost program (list of strings).
          
    """
    fn = 'diagram.mp'
    fbase, _ = os.path.splitext(fn)
    tmpdir = os.tempnam('.', 'piuml')
    shutil.rmtree(tmpdir, ignore_errors=True)
    os.makedirs(tmpdir)

    with open(tmpdir + '/' + fn, 'w') as f:
        for l in data:
            f.write(l)

    try:
        cmd('mptopdf', fn, cwd=tmpdir)
        #cmd('mpost', '-interaction', 'batchmode', fn, tmpdir=tmpdir)
        #cmd('epstopdf', tmpdir + '/' + fbase + '.1', '-o', fout)
        print tmpdir + '/' + fbase + '-1.pdf', fout
        shutil.move(tmpdir + '/' + fbase + '-1.pdf', fout)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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
        cmd('mptopdf', 'sizesT.mp', cwd='.')

        f = csv.reader(open('sizesT.csv'))
        data = {}
        width, height = 0, 0
        for l in f:
            id = l[0]
            t = l[1]
            w, h = float(l[2]), float(l[3])

            if t == 'name':
                style = ast.cache[id].style
                width, height = w, h

                # include icon size
                iw = style.icon_size.width
                ipad = 5
                if iw:
                    width += 2 * iw + 2 * ipad

            elif t == 'compartment':
                style = ast.cache[id].style
                pad = style.padding
                default_w, default_h = style.size
                head = height

                # reset compartments size if there is none
                if ccounts[id] == 1:
                    w, h = 0, 0

                # take head size into account
                w = max(w, width)
                w += pad.left + pad.right
                h += height + ccounts[id] * (pad.top + pad.bottom)
                w, h = max(w, default_w), max(h, default_h)

                # define minimal sizes
                style.min_size = Size(w, h)
                style.size = Size(w, h)
                style.head = head
            else:
                assert False


    def render(self, ast):
        self.preorder(ast)


    def n_diagram(self, node):
        self._def("""
input boxes;
input TEX;

verbatimtex \input amssym etex

prologues:=3;

vardef rotateArrow(text a)(text b) =
enddef;

vardef drawArrow(text a)(text b)(expr closed)(expr filled) =
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
        if filled:
            fill p;
        else:
            unfill p;
        fi
        draw p;
    else:
        draw w[1] -- b -- w[2];
    fi
enddef;

vardef drawDiamond(text a)(text b)(expr filled) =
    numeric alfa;
    alfa = angle(xpart(a - b), ypart(a - b));

    pair w[];
    w[1] := (10, 5);
    w[1] := w[1] rotated (alfa) shifted b;
    w[2] := (-10, 5);
    w[2] := w[2] rotated (180 + alfa) shifted b;
    w[3] := (-20, 0);
    w[3] := w[3] rotated (180 + alfa) shifted b;

    path p;
    p := w[1] -- b -- w[2] -- w[3] -- cycle;
    if filled:
        fill p;
    else:
        unfill p;
    fi
    draw p;
enddef;

vardef drawX(text a)(text b) =
    numeric alfa;
    alfa = angle(xpart(a - b), ypart(a - b));

    pair w[];
    w[1] := (8, -3);
    w[1] := w[1] rotated alfa shifted b;
    w[2] := (2, 3);
    w[2] := w[2] rotated alfa shifted b;

    w[3] := (8, 3);
    w[3] := w[3] rotated alfa shifted b;
    w[4] := (2, -3);
    w[4] := w[4] rotated alfa shifted b;

    draw w[1] -- w[2];
    draw w[3] -- w[4];
enddef;


beginfig(1);

% boxes padding is calculated by us
defaultdx:=0;
defaultdy:=0;

pen defaultpen, iconpen;
defaultpen := pencircle scaled 1pt;
iconpen := pencircle scaled 0.5pt;

pickup defaultpen;
""");


    def n_diagram_exit(self, node):
        for c in node.constraints:
            self._def(c)
        self._draw("""
endfig;
end
""");

        if self.filetype == 'mp':
            with open(self.output, 'w') as f:
                for l in self._defs + self._draws:
                    f.write(l)
                    f.write('\n')
        else:
            save(self.output, self._defs + self._draws)


    def n_element(self, node):
        """
        Draw an element.

        :Parameters:
         node
            piUML language node instance.
        """
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
        self._node(node, comps, border=border, underline=underline, bold=bold)

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
pickup iconpen;
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
pickup defaultpen;
""".format(p=p, w=icon_w, h=icon_h))

        elif node.element == 'artifact':
            p = '{id}.ne - ({ipad}, {ipad})'.format(id=id, ipad=ipad)
            self._draw("""
pickup iconpen;
draw {p} - ({w}, 0) -- {p} - (5, 0)-- {p} - (0, 5)
    -- {p} - (0, {h}) -- {p} - ({w}, {h}) -- cycle;
draw {p} - (5, 0) -- {p} - (5, 5) -- {p} - (0, 5);
pickup defaultpen;
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
        """
        Draw icon-like element.

        :Parameters:
         node
            piUML language node instance representing the element.
        """
        print node.style.ll.x, node.style.ll.y
        print node.style.size
        pos = node.style.ll
        self._draw("""
path pp, pr;
pp := fullcircle scaled 14;
pr := halfcircle scaled 20 rotated 90;
draw pp shifted ({pos.x}, {pos.y});
draw pr shifted ({pos.x}, {pos.y});
path {id}Shape;
pair {id}.required, {id}.provided;
{id}.required := ({pos.x} - 13, {pos.y});
{id}.provided := ({pos.x} + 10, {pos.y});
{id}Shape := {id}.required -- {id}.provided;
draw ({pos.x} - 13, {pos.y}) -- ({pos.x} - 10, {pos.y});
draw ({pos.x} + 7, {pos.y}) -- ({pos.x} + 10, {pos.y});
        """.format(id=id2mp(node.id), pos=pos))


    def n_edge(self, edge):
        """
        Draw an edge.

        :Parameters:
         edge
            piUML edge instance.
        """
        F = {
            'association': self._association,
            'commentline': self._commentline,
            'connector': self._association,
            'dependency': self._dependency,
            'extension': self._association,
            'generalization': self._dependency,
        }
        f = F.get(edge.element)
        if not f:
            print 'WARN: no rendering for edge', edge.element
            return

        f(edge)


    def _node(self, node, comps, border=True, underline=False, bold=True):
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

        # create path
        self._draw("""
path {id}Shape;
{id}Shape := bpath {id};
        """.format(id=id))


    def _name_s(self, node, underline=False, bold=True):
        name = qstr(node.name)
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


    def _association(self, edge):
        """
        Draw association and extension UML lines.

        :Parameters:
         edge
            piUML edge instance.
        """
        if edge.element == 'extension':
            ha = None
            ta = None
            if edge.tail.element == 'metaclass':
                ta = 'blacktriangle'
            elif edge.head.element == 'metaclass':
                ha = 'blacktriangle'
            else:
                assert False

            # draw extension...
            self._edge(edge, tail_arrow=ta, head_arrow=ha)

            # todo: ... and return, with extension typed by an association we
            # will deal in the future
            return
        elif edge.element == 'connector':
            t = edge.tail
            h = edge.head
            iface = ''
            tp = 'c'
            hp = 'c'
            print edge.tail.element, edge.tail.data
            print edge.head.element, edge.head.data
            if t.element == 'fdiface':
                tp = 'provided' if t.data['symbol'] == '(o' else 'required'
                iface = t.name
            if h.element == 'fdiface':
                hp = 'required' if h.data['symbol'] == '(o' else 'provided'
                iface = h.name
            self._edge(edge, tail_point=tp, head_point=hp, label=iface)
            # todo: ... and return, with connector typed by an association we
            # will deal in the future
            return

        END = {
            'none': 'x',
            'shared': 'diamond',
            'composite': 'blackdiamond',
            'navigable': 'arrow',
            'unknown': None,
        }
        ta = END[edge.data['tail'][-1]]
        ha = END[edge.data['head'][-1]]

        name = edge.name
        dir = edge.data['direction']
        if dir is edge.tail:
            name = name + '\\;$\\blacktriangleright$'
        elif dir is edge.head:
            name = '$\\blacktriangleleft$\\;' + name

        self._edge(edge, tail_arrow=ta, head_arrow=ha, label=name)


    def _dependency(self, edge):
        """
        Draw dependency, generalization and realization UML lines.

        :Parameters:
         edge
            piUML edge instance.
        """
        dashed = edge.element != 'generalization'
        ta = None
        ha = 'triangle' if edge.element == 'generalization' else 'arrow'

        st = ''
        if edge.stereotypes:
            stl = edge.stereotypes[:]
            if 'realization' in edge.stereotypes:
                stl.remove('realization')
                ha = 'triangle'
            st = st_fmt(stl)

        if edge.tail is edge.data['supplier']:
            ta, ha = ha, ta
        self._edge(edge, tail_arrow=ta, head_arrow=ha, dashed=dashed, label=st)


    def _commentline(self, edge):
        """
        Draw comment line.

        :Parameters:
         edge
            piUML edge instance.
        """
        self._edge(edge, dashed=True)


    def _edge(self,
            edge,
            tail_point='c',
            head_point='c',
            tail_arrow=None,
            head_arrow=None,
            dashed=False,
            label=''):
        """
        Draw a line for specified edge.

        :Parameters:
         edge
            piUML edge instance.
         tail_point
            Tail connection point.
         head_point
            Head connection point.
         tail_arrow
            Type of arrow to be drawn at edge's tail end.
         head_arrow
            Type of arrow to be drawn at edge's head end.
         dashed
            Draw dashed line if true.
        """
        t = id2mp(edge.tail.id)
        h = id2mp(edge.head.id)

        tp = 'point length tempPath of tempPath'
        hp = 'point 0 of tempPath'
        arrows = {
            'arrow': 'drawArrow{arrow}(false)(false);',
            'triangle': 'drawArrow{arrow}(true)(false);',
            'blacktriangle': 'drawArrow{arrow}(true)(true);',
            'diamond': 'drawDiamond{arrow}(false);',
            'blackdiamond': 'drawDiamond{arrow}(true);',
            'x': 'drawX{arrow};',
        }
        assert tail_arrow is None or tail_arrow in arrows
        assert head_arrow is None or head_arrow in arrows

        ta = arrows.get(tail_arrow)
        if ta:
            ta = ta.format(arrow='(' + tp + ')(' + hp + ')')
        ha = arrows.get(head_arrow)
        if ha:
            ha = ha.format(arrow='(' + hp + ')(' + tp + ')')

        path = """
path tempPath;
tempPath := {t}.{tpoint} -- {h}.{hpoint} cutbefore {t}Shape cutafter {h}Shape;
"""
        path += 'draw tempPath'
        if dashed:
            path += ' dashed evenly scaled 1.2'
        path += ';\n'

        self._draw(path.format(t=t, h=h, tpoint=tail_point, hpoint=head_point))
        if ta:
            self._draw(ta)
        if ha:
            self._draw(ha)

        if label:
            self._draw('label.top(btex {label} etex, 0.5[{tp},{hp}]);'
                    .format(label=label, tp=tp, hp=hp))


# vim: sw=4:et:ai
