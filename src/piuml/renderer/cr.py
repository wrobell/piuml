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
import sys
from cStringIO import StringIO
from spark import GenericASTTraversal
from math import ceil, floor, pi
from functools import partial

from piuml.data import Size, Pos, Style, Area, Node
from piuml.parser import unwind
from piuml.renderer.text import *
from piuml.renderer.shape import *
from piuml.renderer.line import *
from piuml.renderer.util import st_fmt

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
        Calculate minimal size of a node.

        :Parameters:
         node
            Node, which size shall be calculated.
        """
        if node.element == 'actor':
            node.style.size = Size(40, 60)
            return

        cr = self.cr
        pad = node.style.padding
        sizes = [(80, 0)]

        # calculate name size, but include icon size if necessary
        nw, nh = 0, 0 # name size including stereotype
        if node.stereotypes:
            nw, nh = text_size(cr, st_fmt(node.stereotypes), FONT)
        s = text_size(cr, node.name, FONT_NAME) # name size
        nw = max(s[0], nw)
        nh += s[1]
        # include icon size
        ics = node.style.icon_size
        if ics != (0, 0):
            nw += ics[0] + pad.right
            nh = max(nh, ics[1])
        sizes.append(Size(nw, nh))

        compartments = []
        attrs = '\\node'.join(f.name for f in node if f.element == 'attribute')
        opers = '\\node'.join(f.name for f in node if f.element == 'operation')
        cl = 0
        if attrs:
            w, h = text_size(cr, attrs, FONT)
            sizes.append(Size(w, h))
            cl += 1
        if opers:
            w, h = text_size(cr, opers, FONT)
            sizes.append(Size(w, h))
            cl += 1
        st_attrs = (f for f in node if f.element == 'stattributes')
        for f in st_attrs:
            attrs = st_fmt([f.name]) + '\\node' + '\\node'.join(a.name for a in f)
            w, h = text_size(cr, attrs, FONT)
            sizes.append(Size(w, h))
            cl += 1

        width = max(w for w, h in sizes)
        height = sum(h for w, h in sizes) * LINE_STRETCH
        width += pad.left + pad.right
        height += pad.top + pad.bottom + cl * pad.top * 2
        node.style.size = Size(width, max(height, 40))


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

    def dims(self, ast):
        self.calc.calc(ast)

    def render(self, ast):
        self.preorder(ast)


    def _compartment(self, parent, node, filter, skip_top, title=None):
        cr = self.cr
        pos = x, y = parent.style.pos
        size = width, height = parent.style.size
        pad = parent.style.padding

        features = '\\n'.join(f.name for f in node if filter(f))
        if title:
            features = title + features
        if features:
            skip_top += pad.top
            cr.move_to(x, y + skip_top)
            cr.line_to(x + width, y + skip_top)
            skip_top += draw_text(cr, parent.style.size, parent.style,
                    features, skip_top=skip_top, align=(-1, -1))
            skip_top += pad.top
        return skip_top


    def n_element(self, node):

        style = node.style
        pos = x, y = style.pos
        size = width, height = style.size
        pad = style.padding
        iw, ih = style.icon_size

        font = FONT_NAME
        align = (0, -1)
        outside = False
        underline = False
        stereotypes = node.stereotypes[:]
        lskip = 0
        tskip = 0

        cr = self.cr
        cr.save()
        if node.element in ('node', 'device'):
            draw_box3d(cr, pos, size)
        elif node.element in ('package', 'profile'):
            draw_tabbed_box(cr, pos, size)
        elif node.element == 'usecase':
            align = (0, 0)

            r1 = size.width / 2.0
            r2 = size.height / 2.0
            x0 = pos.x + r1
            y0 = pos.y + r2
            draw_ellipse(cr, (x0, y0), r1, r2)
        elif node.element == 'actor':
            align = (0, 1)
            outside = True
            draw_human(cr, pos, size)
        elif node.element == 'comment':
            font = FONT
            draw_note(cr, pos, size)
        elif node.element in ('instance', 'artifact'):
            underline = True
            cr.rectangle(x, y, width, height)
            cr.stroke()
        else:
            cr.rectangle(x, y, width, height)
            cr.stroke()

        # draw icons
        if node.element in ('artifact', 'component'):
            x0 = x + width - iw - pad.top
            y0 = y + pad.top
            if node.element == 'artifact':
                draw_artifact(cr, (x0, y0), (iw, ih))
            else:
                draw_component(cr, (x0, y0), (iw, ih))
            lskip = -(iw + pad.top) / 2.0

        if stereotypes:
            tskip += draw_text(cr, style.size, style,
                    st_fmt(stereotypes),
                    align=align, outside=outside, skip_left=lskip,
                    skip_top=tskip)

        tskip += draw_text(cr, style.size, style,
                node.name,
                font=font, align=align, outside=outside,
                underline=underline,
                skip_top=tskip, skip_left=lskip)

        tskip = max(ih, tskip) # choose between name/stereotype skip and icon height
        tskip += pad.top

        tskip = self._compartment(node, node, lambda f: f.element == 'attribute', tskip)
        tskip = self._compartment(node, node, lambda f: f.element == 'operation', tskip)
        st_attrs = (f for f in node if f.element == 'stattributes')
        for f in st_attrs:
            title = st_fmt([f.name]) + '\\c' 
            tskip = self._compartment(node, f, lambda f: f.element == 'attribute', tskip, title)

        cr.stroke()
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

        draw_text(cr, n.style.size, n.style, n.name, font=FONT_NAME, align=(0, 1), outside=True)


    def n_connector(self, n):
        self._draw_line(n)


    def n_commentline(self, node):
        """
        Draw comment line between elements.
        """
        self._draw_line(node, dash=(7.0, 5.0))


    def n_generalization(self, n):
        if n.data['super'] is n.head:
            self._draw_line(n, draw_head=draw_head_triangle)
        else:
            self._draw_line(n, draw_tail=draw_tail_triangle)


    def n_dependency(self, n):
        supplier = n.data['supplier']
        
        params = {'dash': (7.0, 5.0)}
        if supplier is n.head:
            params['draw_head'] = draw_head_arrow
        else:
            params['draw_tail'] = draw_tail_arrow

        if supplier.element == 'fdiface':
            params = { 'show_st': False }

        if supplier.element in ('interface', 'component'):
            params['show_st'] = False
            if supplier is n.head:
                params['draw_head'] = draw_head_triangle
            else:
                params['draw_tail'] = draw_tail_triangle

        self._draw_line(n, **params)


    def n_association(self, edge):
        """
        Draw association represented by edge.

        :Parameters:
         edge
            Edge representing an association.
        """
        if edge.element == 'extension':
            params = {}
            if edge.tail.element == 'metaclass':
                params['draw_tail'] = partial(draw_tail_arrow, fill=True)
            elif edge.head.element == 'metaclass':
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

        dt = partial(draw_text, self.cr, edge.style.edges, edge.style, align_f=text_pos_at_line)
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
            edge,
            draw_tail=draw_tail_none,
            draw_head=draw_head_none,
            dash=None,
            name_fmt='%s',
            show_st=True):
        """
        Draw line between tail and head of an edge.

        :Parameters:
         edge
            Edge to be drawn.
         draw_tail
            Function used to draw tail of the edge.
         draw_head
            Function used to draw head of the edge.
         name_fmt
            String format used to format name of an edge.
        """
        edges = edge.style.edges
        draw_line(self.cr, edges, draw_tail=draw_tail, draw_head=draw_head, dash=dash)

        text = []
        if show_st and edge.stereotypes:
            text.append(st_fmt(edge.stereotypes))
        if edge.name:
            text.append(name_fmt % edge.name)
        if text:
            text = '\\c'.join(text)
            segment = line_middle_segment(edges)
            draw_text(self.cr, segment, edge.style, text, align=(0, -1), align_f=text_pos_at_line)


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
