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
from gi.repository import Pango

import sys
from io import BytesIO
from math import ceil, floor, pi
from functools import partial

from piuml.data import MWalker, Element, PackagingElement
from piuml.style import Size, Pos, Style, Area
from piuml.renderer.text import *
from piuml.renderer.shape import *
from piuml.renderer.line import *
from piuml.renderer.util import st_fmt

import logging
log = logging.getLogger('piuml.renderer.cr')

def _name(node, bold=True, underline=False, fmt='%s'):
    texts = []
    if node.stereotypes:
        texts.append('<span size="small">%s</span>' \
                % st_fmt(node.stereotypes))
    name = node.name.replace('\\n', '\n')
    if name:
        name = fmt % name
        if bold:
            name = '<b>%s</b>' % name
        if underline:
            name = '<u>%s</u>' % name
        texts.append(name)
    return '\n'.join(texts)


def _features(node, ft):
    return '\n'.join(f.name for f in node.data[ft])


def _head_size(style):
    ph = style.padding.top + style.padding.bottom
    height = style.size.height

    k = len(style.compartment) - 1
    return height - k * ph - sum(style.compartment[1:])


class CairoBBContext(object):
    """
    Delegate all calls to the wrapped CairoBoundingBoxContext, intercept
    ``stroke()``, ``fill()`` and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cr):
        self._cr = cr
        self.bbox = (sys.maxsize, sys.maxsize, 0, 0)

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


class CairoDimensionCalculator(MWalker):
    """
    Node dimension calculator using Cairo.
    """
    def __init__(self):
        super(CairoDimensionCalculator, self).__init__()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        self.cr = CairoBBContext(cairo.Context(self.surface))


    def calc(self, n):
        self.postorder(n)


    def v_element(self, node):
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
        attrs = _features(node, 'attributes')
        opers = _features(node, 'operations')
        if attrs:
            w, h = text_size(cr, attrs)
            sizes.append(Size(w, h))
            style.compartment.append(h)
        if opers:
            w, h = text_size(cr, opers)
            sizes.append(Size(w, h))
            style.compartment.append(h)

        for f in node.data['stattrs']:
            title = '<small>%s</small>\n' % st_fmt([f.name])
            attrs = title + '\n'.join(a.name for a in f)
            w, h = text_size(cr, attrs)
            sizes.append(Size(w, h))
            style.compartment.append(h)

        k = len(style.compartment)
        if isinstance(node, PackagingElement):
            k += 1

        width = max(w for w, h in sizes) + pad.left + pad.right
        height = sum(h for w, h in sizes) + (pad.top + pad.bottom) * k

        style.min_size.width = max(width, style.min_size.width)
        style.min_size.height = max(height, style.min_size.height)


    def v_ielement(self, n):
        n.style.size = Size(36, 36)


    def v_relationship(self, n):
        """
        Calculate length of UML relationship.
        """
        if n.cls in ('association', 'extension'):
            self._association(n)
        else:
            self._set_edge_len(n)

    v_packagingelement = v_diagram = v_element

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
        lens = [text_size(cr, edge.name)[0] + length]
        if edge.stereotypes:
            lens.append(text_size(cr, st_fmt(edge.stereotypes))[0])
        edge.style.min_length = max(75, 2 * sum(lens))
        return sum(lens)


    def _association(self, edge):
        """
        Calculate minimal length of an association line.
        """
        te = edge.data['tail']
        he = edge.data['head']

        # name length taken into account in _set_edge_len
        txt = ''.join(str(t) for t in te[:2] + he[:2] if t)
        w = text_size(self.cr, txt)[0]

        log.debug('calculate size of association "{}": {}'.format(txt, w))
        self._set_edge_len(edge, w)



class CairoRenderer(MWalker):
    """
    Node renderer using Cairo.
    """
    def __init__(self):
        super(CairoRenderer, self).__init__()
        self.calc = CairoDimensionCalculator()
        self.surface = None
        self.cr = None
        self.output = None
        self.filetype = 'pdf'


    def measure(self, ast):
        """
        Calculate minimal size of all diagram nodes.

        :Parameters:
         ast
            Diagram start node.
        """
        self.calc.calc(ast)


    def render(self, ast):
        """
        Render diagram as graphical file.

        :Parameters:
         ast
            Diagram start node.

        .. seealso::
            CairoRenderer.output
            CairoRenderer.filetype
            
        """
        self.preorder(ast)
        self.save_diagram(ast)


    def _compartment(self, parent, features, y0, title=None):
        cr = self.cr
        pos = x, y = parent.style.pos
        size = width, height = parent.style.size
        pad = parent.style.padding

        if title:
            features = title + features
        if features:
            cr.move_to(x, y + y0)
            cr.line_to(x + width, y + y0)
            draw_text(cr, parent.style.size, parent.style,
                    features, pos=(0, y0), align=(-1, -1))


    def v_element(self, node):
        if node.parent.cls == 'align':
            return
        style = node.style
        pos = x, y = style.pos
        width, height = size = style.size
        pad = style.padding
        iw, ih = style.icon_size

        align = (0, 0)
        outside = False
        underline = False
        lalign = pango.Alignment.CENTER
        bold = True
        xskip = 0
        yskip = 0

        cr = self.cr
        cr.save()

        if isinstance(node, PackagingElement):
            align = (0, -1)

        if node.cls in ('node', 'device'):
            draw_box3d(cr, pos, size)
        elif node.cls in ('package', 'profile'):
            draw_tabbed_box(cr, pos, size)
            yskip = 20
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
            lalign = pango.Alignment.LEFT
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
            xskip = -(iw + pad.top) / 2.0

        name = _name(node, bold, underline)

        # calculate height of name from compartment data
        tskip = _head_size(style)
        log.debug('element {} allocated head height {}'.format(name, tskip))

        draw_text(cr, (width, tskip), style,
                name,
                lalign=lalign,
                pos=(xskip, yskip),
                align=align, outside=outside)

        nc = 1
        attrs = _features(node, 'attributes')
        if attrs:
            self._compartment(node, attrs, tskip)
            tskip += style.compartment[nc] + pad.top + pad.bottom
            nc += 1

        opers = _features(node, 'operations')
        if opers:
            self._compartment(node, opers, tskip)
            tskip += style.compartment[nc] + pad.top + pad.bottom
            nc += 1

        for f in node.data['stattrs']:
            title = st_fmt([f.name]) + '\n' 
            attrs = '\n'.join(a.name for a in f)
            self._compartment(node, attrs, tskip, title)
            tskip += style.compartment[nc] + pad.top + pad.bottom
            nc += 1

        cr.restore()

    v_packagingelement = v_element

    def v_ielement(self, n):
        cr = self.cr
        x, y = n.style.pos
        width, height = n.style.size
        nose = 2
        x0 = x + width / 2.0
        y0 = y + height / 2.0
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

        #
        # draw provided/required or assembly interface icons
        #

        # icon drawing functions
        draw_provided = partial(cr.arc, x0, y0, width / 2.0 - nose * 3, 0, pi * 2.0)
        draw_required = partial(cr.arc, x0, y0, height / 2.0 - nose, angle, pi + angle)

        # draw nose
        cr.move_to(x, y0)
        cr.line_to(x + nose, y0)
        cr.move_to(x + width - nose * 3, y0)
        cr.line_to(x + width, y0)
        cr.stroke()

        # draw icons
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

        # draw interface name
        draw_text(cr, n.style.size, n.style, n.name, align=(0, 1), outside=True)


    def v_relationship(self, n):
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

        assert isinstance(edge.head, Element)
        name_fmt = '%s'
        if edge.data['direction'] is edge.head:
            name_fmt = '%s \u25b6'
        else:
            name_fmt = '\u25c0  %s'
            
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
        attr = end[1]
        if attr and attr.name:
            dt(attr.name, align=(halign, -1))
        if attr and attr.mult:
            dt(str(attr.mult), align=(halign, 1))


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
        draw_line(self.cr, line.style.edges, draw_tail=draw_tail, draw_head=draw_head, dash=dash)

        name = _name(line, fmt=name_fmt)
        if name:
            segment = line_middle_segment(line.style.edges)
            draw_text(self.cr, segment, line.style, name, align=(0, -1), align_f=text_pos_at_line)


    def v_diagram(self, n):
        w, h = n.style.size
        w = int(ceil(w))
        h = int(ceil(h))
        self.surface = cairo.PDFSurface(BytesIO(), w * 2, h * 2)
        self.cr = CairoBBContext(cairo.Context(self.surface))
        self.cr.translate(int(w / 4), int(h / 4))
        self.cr.save()


    def save_diagram(self, n):
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
        x1, y1, x2, y2 = list(map(int, (floor(x1), floor(y1), ceil(x2), ceil(y2))))
        w = int(ceil(abs(x2 - x1) * scale))
        h = int(ceil(abs(y2 - y1) * scale))

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
