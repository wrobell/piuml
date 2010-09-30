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
piUML Cairo renderer.

Drawing routines are adapted from Gaphas and Gaphor source code.
"""

import cairo
import pango

import sys
from cStringIO import StringIO
from spark import GenericASTTraversal
from math import ceil, floor, pi
from functools import partial

from piuml.data import Size, Pos, Style, Area, Node
from piuml.renderer.text import *
from piuml.renderer.shape import *
from piuml.renderer.line import *
from piuml.renderer.util import st_fmt


def _name(node, bold=True, underline=False):
    texts = []
    if node.stereotypes:
        texts.append('<span size="small">%s</span>' \
                % st_fmt(node.stereotypes))
    name = node.name.replace('\\n', '\n')
    if name:
        if bold:
            name = '<b>%s</b>' % name
        if underline:
            name = '<u>%s</u>' % name
        texts.append(name)
    return '\n'.join(texts)


class CairoBBContext(object):
    """
    Delegate all calls to the wrapped CairoBoundingBoxContext, intercept
    ``stroke()``, ``fill()`` and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cr):
        self._cr = cr
        self.bbox = (sys.maxint, sys.maxint, 0, 0)

    def __getattr__(self, key):
        return getattr(self._cr, key)

    def _update_bbox(self, bbox):
        if bbox == (0, 0, 0, 0):
            return
        x1, y1, x2,  y2 = bbox
        xb1, yb1, xb2, yb2 = self.bbox
        self.bbox = min(x1, xb1), min(y1, yb1), max(x2, xb2), max(y2, yb2)


    def _bbox(self, f):
        """
        Calculate the bounding box for a given drawing operation.
        if ``line`` is True, the current line-width is taken into account.
        """
        cr = self._cr
        cr.save()
        cr.identity_matrix()
        bbox = f()
        cr.restore()
        self._update_bbox(bbox)
        return bbox

    def fill(self):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        self._bbox(cr.fill_extents)
        cr.fill()

    def fill_preserve(self):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        self._bbox(cr.fill_extents)
        cr.fill_preserve()

    def stroke(self, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        self._bbox(cr.stroke_extents)
        cr.stroke()

    def stroke_preserve(self):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        self._bbox(cr.stroke_extents)
        cr.stroke_preserve()

    def show_text(self, txt):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        x, y = cr.get_current_point()
        e = cr.text_extents(txt)
        x1, y1 = cr.user_to_device(x + e[0], y + e[1])
        x2, y2 = cr.user_to_device(x + e[0] + e[2], y + e[1] + e[3])
        bbox = x1 - 2, y1 - 2, x2 + 2, y2 + 2
        self._update_bbox(bbox)
        cr.show_text(txt)


class CairoDimensionCalculator(GenericASTTraversal):
    """
    Node dimension calculator using Cairo.
    """
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        self.cr = cairo.Context(self.surface)


    def calc(self, ast):
        self.postorder(ast)


    def n_element(self, node):
        """
        Calculate minimal size of an element.

        :Parameters:
         node
            Node, which size shall be calculated.
        """
        if node.cls == 'actor':
            node.style.size = Size(40, 60)
            return

        cr = self.cr
        style = node.style
        pad = style.padding
        sizes = []

        # calculate name size, but include icon size if necessary
        name = _name(node)
        nw, nh = text_size(cr, name)

        # include icon size
        ics = style.icon_size
        if ics != (0, 0):
            nw += ics.width + pad.right
            nh = max(nh, ics.height)
        style.compartment[0] = nh
        sizes.append(Size(nw, nh))

        compartments = []
        attrs = '\n'.join(f.name for f in node if f.cls == 'attribute')
        opers = '\n'.join(f.name for f in node if f.cls == 'operation')
        if attrs:
            w, h = text_size(cr, attrs)
            sizes.append(Size(w, h))
            style.compartment.append(h)
        if opers:
            w, h = text_size(cr, opers)
            sizes.append(Size(w, h))
            style.compartment.append(h)
        st_attrs = (f for f in node if f.cls == 'stattributes')
        for f in st_attrs:
            title = '<small>%s</small>\n' % st_fmt([f.name])
            attrs = title + '\n'.join(a.name for a in f)
            w, h = text_size(cr, attrs)
            sizes.append(Size(w, h))
            style.compartment.append(h)

        k = len(style.compartment)
        if node.is_packaging():
            k += 1

        width = max(w for w, h in sizes) + pad.left + pad.right
        height = sum(h for w, h in sizes) + (pad.top + pad.bottom) * k

        style.min_size.width = max(width, style.min_size.width)
        style.min_size.height = max(height, style.min_size.height)


    def n_ielement(self, n):
        n.style.size = Size(28, 28)


    def _set_edge_len(self, edge, length=0):
        """
        Calculate and set minimal length of an edge.

        :Parameters:
         edge
            Edge, which length shall be calculated.
         length
            Additional length to be added to calculated length.
        """
        cr = self.cr
        lens = [text_size(cr, edge.name, FONT)[0] + length]
        if edge.stereotypes:
            lens.append(text_size(cr, st_fmt(edge.stereotypes), FONT)[0])
        l = max(75, 2 * sum(lens))
        edge.style.size = Size(l, 0)
        return sum(lens)


    def n_dependency(self, edge):
        """
        Calculate minimal length of a dependency line.
        """
        self._set_edge_len(edge)

    n_commentline = n_connector = n_generalization = n_dependency

    def n_association(self, edge):
        """
        Calculate minimal length of an association line.
        """
        te = edge.data['tail']
        he = edge.data['head']
        txt = ''.join(t for t in te[:3] + he[:3] if t)
        self._set_edge_len(edge, text_size(self.cr, txt, FONT)[0])



class CairoRenderer(GenericASTTraversal):
    """
    Node renderer using Cairo.
    """
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self.calc = CairoDimensionCalculator()
        self.surface = None
        self.cr = None
        self.output = None
        self.filetype = 'pdf'

    def constraint(self, ast):
        self.calc.calc(ast)

    def render(self, ast):
        self.preorder(ast)


    def _compartment(self, parent, node, filter, skip_top, title=None):
        cr = self.cr
        pos = x, y = parent.style.pos
        size = width, height = parent.style.size
        pad = parent.style.padding

        features = '\n'.join(f.name for f in node if filter(f))
        if title:
            features = title + features
        if features:
            skip_top += pad.top
            cr.move_to(x, y + skip_top)
            cr.line_to(x + width, y + skip_top)
            skip_top += draw_text(cr._cr, parent.style.size, parent.style,
                    features, pos=(0, skip_top), align=(-1, -1))
            skip_top += pad.top
        return skip_top


    def n_element(self, node):

        style = node.style
        pos = x, y = style.pos
        width, height = size = style.size
        pad = style.padding
        iw, ih = style.icon_size

        align = (0, -1)
        outside = False
        underline = False
        lalign = pango.ALIGN_CENTER
        bold = True
        lskip = 0

        cr = self.cr
        cr.save()
        if node.cls in ('node', 'device'):
            draw_box3d(cr, pos, size)
        elif node.cls in ('package', 'profile'):
            draw_tabbed_box(cr, pos, size)
        elif node.cls == 'usecase':
            align = (0, 0)

            r1 = size.width / 2.0
            r2 = size.height / 2.0
            x0 = pos.x + r1
            y0 = pos.y + r2
            draw_ellipse(cr, (x0, y0), r1, r2)
        elif node.cls == 'actor':
            align = (0, 1)
            outside = True
            draw_human(cr, pos, size)
        elif node.cls == 'comment':
            draw_note(cr, pos, size)
            lalign = pango.ALIGN_LEFT
            bold = False
        elif node.cls in ('instance', 'artifact'):
            underline = True
            cr.rectangle(x, y, width, height)
            cr.stroke()
        else:
            cr.rectangle(x, y, width, height)
            cr.stroke()

        # draw icons
        if node.cls in ('artifact', 'component'):
            x0 = x + width - iw - pad.top
            y0 = y + pad.top
            if node.cls == 'artifact':
                draw_artifact(cr, (x0, y0), (iw, ih))
            else:
                draw_component(cr, (x0, y0), (iw, ih))
            lskip = -(iw + pad.top) / 2.0

        name = _name(node, bold, underline)
        draw_text(cr._cr, style.size, style,
                name,
                lalign=lalign,
                pos=(lskip, 0),
                align=align, outside=outside)

        k = len(style.compartment) - 1
        comps = sum(style.compartment[1:]) if k else 0 # height of compartments
        tskip = height - k * (pad.top + pad.bottom) - comps

        tskip = self._compartment(node, node, lambda f: f.cls == 'attribute', tskip)
        tskip = self._compartment(node, node, lambda f: f.cls == 'operation', tskip)
        st_attrs = (f for f in node if f.cls == 'stattributes')
        for f in st_attrs:
            title = st_fmt([f.name]) + '\n' 
            tskip = self._compartment(node, f, lambda f: f.cls == 'attribute', tskip, title)

        cr.restore()


    def n_ielement(self, n):
        cr = self.cr
        x, y = n.style.pos
        x0 = x + 14 
        y0 = y + 14
        angle = pi / 2.0

        is_assembly = n.data['assembly'] is not None
        if is_assembly:
            is_usage = False
            if n.data['symbol'] == 'o)':
                angle = -angle
        else:
            dep = n.data['dependency']
            is_usage = 'use' in dep.stereotypes
            if dep.tail is n:
                angle = -angle

        draw_provided = partial(cr.arc, x0, y0, 10, 0, pi * 2.0)
        draw_required = partial(cr.arc, x0, y0, 14, angle, pi + angle)

        #
        # draw provided/required or assembly interface icons
        #

        # first draw lines to the middle of icon
        for l in n.data['lines']:
            i = -1 if l.head is n else 0
            line = (l.style.edges[i], (x0, y0))
            draw_line(cr, line)

        # then erase lines, so they touch only the icon shape
        cr.save()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        draw_provided()
        cr.fill()
        if is_assembly or is_usage:
            draw_required()
            cr.close_path()
            cr.fill()
        cr.restore()

        # finally, draw the shape
        cr.save()
        if is_usage or is_assembly:
            cr.save()
            draw_required()
            cr.stroke()
            cr.restore()
        if not is_usage or is_assembly:
            cr.save()
            draw_provided()
            cr.stroke()
            cr.restore()

        draw_text(cr, n.style.size, n.style, n.name, align=(0, 1), outside=True)


    def n_line(self, n):
        t = '_' + n.cls
        if n.cls == 'extension':
            t = '_association'
        f = getattr(self, t)
        f(n)


    def _connector(self, n):
        self._draw_line(n)


    def _commentline(self, node):
        """
        Draw comment line between elements.
        """
        self._draw_line(node, dash=(7.0, 5.0))


    def _generalization(self, n):
        if n.data['supplier'] is n.head:
            self._draw_line(n, draw_head=draw_head_triangle)
        else:
            self._draw_line(n, draw_tail=draw_tail_triangle)


    def _dependency(self, n):
        supplier = n.data['supplier']
        
        params = {'dash': (7.0, 5.0)}
        if supplier is n.head:
            params['draw_head'] = draw_head_arrow
        else:
            params['draw_tail'] = draw_tail_arrow

        if supplier.cls == 'fdiface':
            params = { 'show_st': False }

        if supplier.cls in ('interface', 'component'):
            params['show_st'] = False
            if supplier is n.head:
                params['draw_head'] = draw_head_triangle
            else:
                params['draw_tail'] = draw_tail_triangle

        self._draw_line(n, **params)


    def _association(self, edge):
        """
        Draw association represented by edge.

        :Parameters:
         edge
            Edge representing an association.
        """
        if edge.cls == 'extension':
            params = {}
            if edge.tail.cls == 'metaclass':
                params['draw_tail'] = partial(draw_tail_arrow, fill=True)
            elif edge.head.cls == 'metaclass':
                params['draw_head'] = partial(draw_head_arrow, fill=True)
            else:
                assert False
            self._draw_line(edge, **params)
            return

        TEND = {
            'none': draw_tail_x,
            'shared': draw_tail_diamond,
            'composite': partial(draw_tail_diamond, filled=True),
            'navigable': draw_tail_arrow,
            'unknown': draw_tail_none,
        }
        HEND = {
            'none': draw_head_x,
            'shared': draw_head_diamond,
            'composite': partial(draw_head_diamond, filled=True),
            'navigable': draw_head_arrow,
            'unknown': draw_head_none,
        }
        dt = TEND[edge.data['tail'][-1]]
        dh = HEND[edge.data['head'][-1]]

        dir = edge.data['direction']
        name_fmt = '%s'
        if dir and dir == 'head':
            name_fmt = u'%s \u25b6'
        else:
            name_fmt = u'\u25c0  %s'
            
        self._draw_line(edge, draw_tail=dt, draw_head=dh, name_fmt=name_fmt)

        dt = partial(draw_text, self.cr._cr, edge.style.edges, edge.style, align_f=text_pos_at_line)
        self._draw_association_end(dt, edge.data['tail'], -1)
        self._draw_association_end(dt, edge.data['head'], 1)


    def _draw_association_end(self, dt, end, halign):
        """
        Draw association end.

        :Parameters:
         dt
            Function used to draw association end text.
         end
            Tuple containing association end data.
         halign
            Horizontal alignment of the association end.
        """
        c, n, m, _ = end
        if n:
            dt(n, align=(halign, -1))
        if m:
            dt(m, align=(halign, 1))


    def _draw_line(self,
            line,
            draw_tail=draw_tail_none,
            draw_head=draw_head_none,
            dash=None,
            name_fmt='%s',
            show_st=True):
        """
        Draw line between tail and head of an edge.

        :Parameters:
         line
            Line to draw.
         draw_tail
            Function used to draw tail of the edge.
         draw_head
            Function used to draw head of the edge.
         name_fmt
            String format used to format name of an edge.
        """
        #edges = line.style.edges
        # FIXME: code cleanup
        t, h = line.tail, line.head
        def get_cp(node):
            x1, y1 = node.style.pos
            w, h = node.style.size
            x2 = x1 + w
            y2 = y1 + h
            x = (x1 + x2) / 2.0
            y = (y1 + y2) / 2.0
            return (x1, y), (x2, y), (x, y1), (x, y2)

        def shortest(t, h):
            r = sorted(get_cp(t) + get_cp(h))
            return r[len(r) / 2 - 1], r[len(r) / 2]

        edges = shortest(t, h)
        draw_line(self.cr, edges, draw_tail=draw_tail, draw_head=draw_head, dash=dash)

        name = _name(line)
        if name:
            segment = line_middle_segment(edges)
            draw_text(self.cr._cr, segment, line.style, name, align=(0, -1), align_f=text_pos_at_line)


    def n_diagram(self, n):
        w, h = n.style.size
        w = int(ceil(w))
        h = int(ceil(h))
        self.surface = cairo.PDFSurface(StringIO(), w * 2, h * 2)
        self.cr = CairoBBContext(cairo.Context(self.surface))
        self.cr.translate(int(w / 4), int(h / 4))
        self.cr.save()


    def n_diagram_exit(self, n):
        """
        Generate PDF, SVG or PNG file with UML diagram.
        """
        # match size of vector and raster output on screen
        DPI = 96.0
        scale = 1.0
        if self.filetype != 'png':
            scale = 72.0 / DPI

        self.cr.restore()

        x1, y1, x2, y2 = self.cr.bbox
        x1, y1, x2, y2 = map(int, (floor(x1), floor(y1), ceil(x2), ceil(y2)))
        w = abs(x2 - x1) * scale
        h = abs(y2 - y1) * scale

        if self.filetype == 'png':
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        elif self.filetype == 'svg':
            s = cairo.SVGSurface(self.output, w, h)
        else:
            s = cairo.PDFSurface(self.output, w, h)

        cr = cairo.Context(s)
        cr.scale(scale, scale)
        cr.set_source_surface(self.surface, -x1, -y1)
        cr.paint()
        cr.show_page()
        if self.filetype == 'png':
            s.write_to_png(self.output)

        self.surface.flush()
        self.surface.finish()

        s.flush()
        s.finish()


# vim: sw=4:et:ai