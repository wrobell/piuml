"""
piUML Cairo renderer.

Drawing routines are adapted from Gaphas and Gaphor source code.
"""

import cairo
import re
from cStringIO import StringIO
from spark import GenericASTTraversal
from math import atan2, ceil, floor, pi
from functools import partial

from piuml.parser import Size, Pos, Style, Node, unwind

# Default font
FONT = 'sans 10'

# Default font for abstract named (e.g. attributes)
FONT_ABSTRACT = 'sans italic 10'

# Font for names of elements (such as classes)
FONT_NAME = 'sans bold 10'

# Abstract classes use this font for their name
FONT_ABSTRACT_NAME = 'sans bold italic 10'

# Small text, e.g. the (from ...) line in classes
FONT_SMALL = 'sans 8'

LINE_STRETCH=1.0

DEBUG = False

class CairoBBContext(object):
    """
    Delegate all calls to the wrapped CairoBoundingBoxContext, intercept
    ``stroke()``, ``fill()`` and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cr):
        self._cr = cr
        self.bbox = (0, 0, 0, 0)

    def __getattr__(self, key):
        return getattr(self._cr, key)

    def _update_bbox(self, bbox):
        x1, y1, x2,  y2 = bbox
        xb1, yb1, xb2, yb2 = self.bbox
        self.bbox = min(x1, xb1), min(y1, yb1), max(x2, xb2), max(y2, yb2)


    def _bbox(self, f, line=False):
        """
        Calculate the bounding box for a given drawing operation.
        if ``line`` is True, the current line-width is taken into account.
        """
        cr = self._cr
        cr.save()
        cr.identity_matrix()
        bbox = f()
        cr.restore()

        if line:
            lw = cr.get_line_width() / 2.0
            d = cr.user_to_device_distance(lw, lw)
            db = d[0] + d[1]
            x1, y1, x2, y2 = bbox
            bbox = x1 - db, y1 - db, x2 + db, y2 + db
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
        self._bbox(cr.stroke_extents, line=True)
        cr.stroke()

    def stroke_preserve(self):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cr
        self._bbox(cr.stroke_extents, line=True)
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



def draw_line_end(cr, pos, angle, draw):
    cr.save()
    try:
        cr.translate(*pos)
        cr.rotate(angle)
        draw(cr)
    finally:
        cr.restore()


def draw_head_none(cr):
    """
    Default head drawer: move cursor to the first handle.
    """
    cr.line_to(0, 0)


def draw_tail_none(cr):
    """
    Default tail drawer: draw line to the last handle.
    """
    cr.stroke()
    cr.move_to(0, 0)


def draw_head_x(cr):
    """
    Draw an 'x' on the line end to indicate no navigability at
    association head.
    """
    cr.line_to(0, 0)
    cr.move_to(6, -4)
    cr.rel_line_to(8, 8)
    cr.rel_move_to(0, -8)
    cr.rel_line_to(-8, 8)
    cr.stroke()


def draw_tail_x(cr):
    """
    Draw an 'x' on the line end to indicate no navigability at
    association tail.
    """
    cr.move_to(6, -4)
    cr.rel_line_to(8, 8)
    cr.rel_move_to(0, -8)
    cr.rel_line_to(-8, 8)
    cr.stroke()
    cr.move_to(0, 0)


def draw_diamond(cr):
    """
    Helper function to draw diamond shape for shared and composite
    aggregations.
    """
    cr.move_to(20, 0)
    cr.line_to(10, -6)
    cr.line_to(0, 0)
    cr.line_to(10, 6)
    cr.close_path()


def draw_head_diamond(cr, filled=False):
    """
    Draw a closed diamond on the line end to indicate composite
    aggregation at association head.
    """
    cr.line_to(20, 0)
    cr.stroke()
    draw_diamond(cr)
    if filled:
        cr.fill_preserve()
    cr.stroke()


def draw_tail_diamond(cr, filled=False):
    """
    Draw a closed diamond on the line end to indicate composite
    aggregation at association tail.
    """
    draw_diamond(cr)
    if filled:
        cr.fill_preserve()
    cr.stroke()
    cr.move_to(20, 0)


def draw_head_arrow(cr):
    """
    Draw a normal arrow to indicate association end navigability at
    association head.
    """
    dash = cr.get_dash()
    #cr.set_dash((), 0)
    cr.line_to(0, 0)
    cr.stroke()
    cr.move_to(15, -6)
    cr.line_to(0, 0)
    cr.line_to(15, 6)
    cr.stroke()
    #cr.set_dash(*dash)


def draw_tail_arrow(cr):
    """
    Draw a normal arrow to indicate association end navigability at
    association tail.
    """
    dash = cr.get_dash()
    #cr.set_dash((), 0)
    cr.move_to(15, -6)
    cr.line_to(0, 0)
    cr.line_to(15, 6)
    cr.stroke()
    cr.move_to(0, 0)
    #cr.set_dash(*dash)


def draw_triangle(cr):
    cr.move_to(0, 0)
    cr.line_to(15, -10)
    cr.line_to(15, 10)
    cr.close_path()
    cr.stroke()
    cr.move_to(15, 0)


def draw_line(cr, edges, draw_tail=draw_tail_none, draw_head=draw_head_none, dash=None):
    p0, p1 = edges[:2]
    t_angle = atan2(p1[1] - p0[1], p1[0] - p0[0])
    p1, p0 = edges[-2:]
    h_angle = atan2(p1[1] - p0[1], p1[0] - p0[0])

    cr.save()
    draw_line_end(cr, edges[0], t_angle, draw_tail)
    if dash is not None:
        cr.set_dash(dash, 0)
    for x, y in edges[1:-1]:
        cr.line_to(x, y)
    draw_line_end(cr, edges[-1], h_angle, draw_head)
    cr.stroke()
    cr.restore()


def box3d(cr, pos, size):
    cr.save()
    d = 10
    x, y = pos
    w, h = size

    cr.rectangle(x, y, w, h)
    cr.move_to(x, y)
    cr.line_to(x + d, y - d)
    cr.line_to(x + w + d, y - d)
    cr.line_to(x + w + d, y + h - d)
    cr.line_to(x + w, y + h)
    cr.move_to(x + w, y)
    cr.line_to(x + w + d, y - d)
    cr.stroke()
    cr.restore()


def text_size(cr, txt, font):
    """
    Calculate total size of a text for specified font.

    Text can be multiline - '\n', '\c' and '\r' are recognized as end of
    line.
    """
    cr.save()
    set_font(cr, font)
    txts = re.split(r'\\[cnr]', txt)
    widths = [cr.text_extents(t)[0] + cr.text_extents(t)[-2] for t in txts] 
    height = cr.font_extents()[2] * len(txts)
    cr.restore()
    return max(widths), height


def set_font(cr, font):
    """
    Set the font from a string. E.g. 'sans 10' or 'sans italic bold 12'
    only restriction is that the font name should be the first option and
    the font size as last argument
    """
    font = font.split()
    cr.select_font_face(font[0],
        cairo.FONT_SLANT_ITALIC if 'italic' in font else cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD  if 'bold' in font else cairo.FONT_WEIGHT_NORMAL)
    size = float(font[-1])
    cr.set_font_size(size)
    return float(font[-1])


def text_pos_at_box(style, size, align, outside=False):
    """
    Calculate position of the text relative to containing box.
    """
    #x_bear, y_bear, w, h, x_adv, y_adv = extents
    w, h = size
    x0, y0 = style.pos
    width, height = style.size
    pad = style.padding

    halign, valign = align

    # horizontal align
    ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = -1, 0, 1
    # vertical align
    ALIGN_TOP, ALIGN_MIDDLE, ALIGN_BOTTOM = -1, 0, 1

    if outside:
        if halign == ALIGN_LEFT:
            x = -w - pad.left
        elif halign == ALIGN_CENTER:
            x = (width - w) / 2
        elif halign == ALIGN_RIGHT:
            x = width + pad.right
        else:
            assert False

        if valign == ALIGN_TOP:
            y = -pad.top
        elif valign == ALIGN_MIDDLE:
            y = height / 2.0
        elif valign == ALIGN_BOTTOM:
            y = height + pad.bottom
        else:
            assert False
    else:
        if halign == ALIGN_LEFT:
            x = pad.left
        elif halign == ALIGN_CENTER:
            x = (width - w) / 2.0 + pad.left - pad.right
        elif halign == ALIGN_RIGHT:
            x = width - w - pad.right
        else:
            assert False

        if valign == ALIGN_TOP:
            y = pad.top
        elif valign == ALIGN_MIDDLE:
            y = height / 2
        elif valign == ALIGN_BOTTOM:
            y = height - pad.bottom
        else:
            assert False
    return x + x0, y + y0



def text_pos_at_line(style, p1, p2):
    """
    Calculate position of the text relative to a line defined by points
    (p1, p2). Text is aligned using align and padding information. 

    :Parameters:
     style
         Text style information like position, size, etc.
     p1
         Beginning of line.
     p2
         End of line.
    """
    EPSILON = 1e-6

    # horizontal align
    ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = -1, 0, 1
    # vertical align
    ALIGN_TOP, ALIGN_MIDDLE, ALIGN_BOTTOM = -1, 0, 1

    # hint tuples to move text depending on quadrant
    WIDTH_HINT = (0, 0, -1)    # width hint tuple
    R_WIDTH_HINT = (-1, -1, 0)    # width hint tuple
    PADDING_HINT = (1, 1, -1)  # padding hint tuple

    x0 = (p1[0] + p2[0]) / 2.0
    y0 = (p1[1] + p2[1]) / 2.0
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    if abs(dx) < EPSILON:
        d1 = -1.0
        d2 = 1.0
    elif abs(dy) < EPSILON:
        d1 = 0.0
        d2 = 0.0
    else:
        d1 = dy / dx
        d2 = abs(d1)

    pad = style.padding
    width, height = style.size
    halign, valign = ALIGN_CENTER, ALIGN_TOP

    # move to center and move by delta depending on line angle
    if d2 < 0.5774: # <0, 30>, <150, 180>, <-180, -150>, <-30, 0>
        # horizontal mode
        w2 = width / 2.0
        hint = w2 * d2

        x = x0 - w2
        if valign == ALIGN_TOP:
            y = y0 - pad.bottom - hint
        else:
            y = y0 + pad.top + hint + height
    else:
        # much better in case of vertical lines

        # determine quadrant, we are interested in 1 or 3 and 2 or 4
        # see hint tuples below
        h2 = height / 2.0
        q = cmp(d1, 0)
        if abs(dx) < EPSILON:
            hint = 0
        else:
            hint = h2 / d2

        if valign == ALIGN_TOP:
            x = x0 + PADDING_HINT[q] * (pad.left + hint) + width * WIDTH_HINT[q]
        else:
            x = x0 - PADDING_HINT[q] * (pad.right + hint) + width * R_WIDTH_HINT[q]
        y = y0 - h2

    return x, y


def line_middle_segment(edges):
    """
    Get positions of middle segment of a line represented by specified
    edges.
    """
    med = len(edges) / 2
    p1, p2 = edges[med - 1: med + 1]
    return p1, p2


def line_center(edges):
    """
    Get mid point and angle of middle segment of a line defined by
    specified edges.
    """
    p1, p2 = line_middle_segment(edges)
    pos = (p1.x + p2.x) / 2, (p1.y + p2.y) / 2
    angle = atan2(p2.y - p1.y, p2.x - p1.x)
    return pos, angle


def draw_text(cr, style, txt, font=FONT, top=0, align=(0, -1), outside=False):
    h, v = align
    set_font(cr, font)
    TALIGN = { -1: 'n', 0: 'c', 1: 'r', }
    ALIGN = { 'n': -1, 'c': 0, 'r': 1, }

    txts = re.split(r'\\[ncr]', txt)
    ends = re.findall(r'\\([ncr])', txt) + [TALIGN[h]]

    skip = 0
    for t, e in zip(txts, ends):
        h = ALIGN[e]

        size = text_size(cr, t, font)
        x0, y0 = text_pos_at_box(style, size, align=(h, v), outside=outside)

        skip += size[1] * LINE_STRETCH
        y = y0 + top + skip

        cr.save()
        cr.move_to(x0, y - 2) # little hack as text appears bit below than expected, to be fixed
        cr.show_text(t)
        cr.restore()

    return skip



def fmts(stereotypes):
    """
    Format list of stereotypes.
    """
    return '\xc2\xab%s\xc2\xbb' % ', '.join(stereotypes)


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

    def n_element(self, n):
        cr = self.cr
        pad = n.style.padding
        sizes = [(80, 0)]

        if n.stereotypes:
            sizes.append(text_size(cr, fmts(n.stereotypes), FONT))
        sizes.append(text_size(cr, n.name, FONT_NAME))

        compartments = []
        attrs = '\\n'.join(f.name for f in n if f.element == 'attribute')
        opers = '\\n'.join(f.name for f in n if f.element == 'operation')
        cl = 0
        if attrs:
            w, h = text_size(cr, attrs, FONT)
            sizes.append(Size(w, h))
            cl += 1
        if opers:
            w, h = text_size(cr, opers, FONT)
            sizes.append(Size(w, h))
            cl += 1
        st_attrs = (f for f in n if f.element == 'stattributes')
        for f in st_attrs:
            attrs = fmts([f.name]) + '\\n' + '\\n'.join(a.name for a in f)
            w, h = text_size(cr, attrs, FONT)
            sizes.append(Size(w, h))
            cl += 1

        width = max(w for w, h in sizes)
        height = sum(h for w, h in sizes) * LINE_STRETCH
        width += pad.left + pad.right
        height += pad.top + pad.bottom + cl * pad.top * 2
        n.style.size = Size(width, max(height, 40))


    def n_ielement(self, n):
        n.style.size = Size(28, 28)



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


    def _compartment(self, parent, node, filter, skip, title=None):
        cr = self.cr
        pos = x, y = parent.style.pos
        size = width, height = parent.style.size
        pad = parent.style.padding

        features = '\\n'.join(f.name for f in node if filter(f))
        if title:
            features = title + features
        if features:
            skip += pad.top
            cr.move_to(x, y + skip)
            cr.line_to(x + width, y + skip)
            if DEBUG:
                cr.move_to(x + pad.left, y + skip + pad.top)
                cr.line_to(x + width - pad.right, y + skip + pad.top)
            skip += draw_text(cr, parent.style, features, top=skip, align=(-1, -1))
            skip += pad.top
        return skip


    def n_element(self, node):
        pos = x, y = node.style.pos
        size = width, height = node.style.size
        pad = node.style.padding
        font = FONT_NAME

        cr = self.cr
        cr.save()
        if node.element in ('node', 'device'):
            box3d(cr, pos, size)
            cr.stroke()
        elif node.element == 'comment':
            font = FONT
            ear = 15
            w = x + width
            h = y + height
            cr.move_to(w - ear, y)
            line_to = cr.line_to
            line_to(w - ear, y + ear)
            line_to(w, y + ear)
            line_to(w - ear, y)
            line_to(x, y)
            line_to(x, h)
            line_to(w, h)
            line_to(w, y + ear)
            cr.stroke()
        else:
            cr.rectangle(x, y, width, height)
            cr.stroke()
            if DEBUG:
                cr.save()
                cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
                cr.rectangle(x + pad.left, y + pad.top, width - pad.left - pad.right, height - pad.top - pad.bottom)
                cr.stroke()
                cr.restore()

        skip = 0
        if node.stereotypes:
            skip += draw_text(cr, node.style, fmts(node.stereotypes))
        skip += draw_text(cr, node.style, node.name, font=font, top=skip)
        skip += pad.top
        if DEBUG:
            cr.save()
            cr.set_source_rgba(0.0, 1.0, 0.0, 0.5)
            cr.move_to(x + pad.left, y + skip)
            cr.line_to(x - pad.right + width, y + skip)
            cr.stroke()
            cr.restore()

        skip = self._compartment(node, node, lambda f: f.element == 'attribute', skip)
        skip = self._compartment(node, node, lambda f: f.element == 'operation', skip)
        st_attrs = (f for f in node if f.element == 'stattributes')
        for f in st_attrs:
            title = fmts([f.name]) + '\\c' 
            skip = self._compartment(node, f, lambda f: f.element == 'attribute', skip, title)

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

        draw_text(cr, n.style, n.name, font=FONT_NAME, align=(0, 1), outside=True)


    def n_connector(self, n):
        self._draw_line(n)


    def n_commentline(self, node):
        """
        Draw comment line between elements.
        """
        self._draw_line(node, dash=(7.0, 5.0))


    def n_generalization(self, n):
        if n.data['super'] is n.head:
            self._draw_line(n, draw_head=draw_triangle)
        else:
            self._draw_line(n, draw_tail=draw_triangle)


    def n_dependency(self, n):
        supplier = n.data['supplier']
        
        params = {'dash': (7.0, 5.0)}
        if supplier is n.head:
            params['draw_head'] = draw_head_arrow
        else:
            params['draw_tail'] = draw_tail_arrow

        if supplier.element == 'fdiface':
            params = { 'show_st': False }

        self._draw_line(n, **params)


    def n_association(self, edge):
        """
        Draw association represented by edge.

        :Parameters:
         edge
            Edge representing an association.
        """
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
        dt = TEND[edge.data['tail']]
        dh = HEND[edge.data['head']]

        dir = edge.data['direction']
        name_fmt = '%s'
        if dir and dir == 'head':
            name_fmt = u'%s \u25b6'
        else:
            name_fmt = u'\u25c0  %s'
            
        self._draw_line(edge, draw_tail=dt, draw_head=dh, name_fmt=name_fmt)


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
        self.cr.save()
        draw_line(self.cr, edges, draw_tail=draw_tail, draw_head=draw_head, dash=dash)

        text = []
        if edge.stereotypes:
            text.append(fmts(edge.stereotypes))

        if edge.name:
            text.append(name_fmt % edge.name)

        if text:
            text = '\\c'.join(text)
            style = Style()
            style.padding = edge.style.padding
            style.margin = edge.style.margin
            style.size = Size(*text_size(self.cr, text, FONT))

            p1, p2 = line_middle_segment(edges)

            x, y = text_pos_at_line(style, p1, p2)
            cr = self.cr
            cr.save()
            cr.move_to(x, y)
            set_font(cr, FONT)
            cr.show_text(text)
            cr.stroke()
            cr.restore()

        self.cr.stroke()
        self.cr.restore()


    def n_diagram(self, n):
        w, h = n.style.size
        w = int(ceil(w))
        h = int(ceil(h))
        self.origin = int(floor(w / 4.0)), int(floor(h / 4.0))
        self.surface = cairo.PDFSurface(StringIO(), w * 2, h * 2)
        self.cr = CairoBBContext(cairo.Context(self.surface))
        self.cr.translate(*self.origin)
        self.cr.save()


    def n_diagram_exit(self, n):
        """
        Generate PDF, SVG or PNG file with UML diagram.
        """
        self.cr.restore()
        x0, y0 = self.origin

        x1, y1, x2, y2 = self.cr.bbox
        x1, y1, x2, y2 = map(int, (floor(x1), floor(y1), ceil(x2), ceil(y2)))
        w = abs(x2 - x1) - x0
        h = abs(y2 - y1) - y0

        if self.filetype == 'png':
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        elif self.filetype == 'svg':
            s = cairo.SVGSurface(self.output, w, h)
        else:
            s = cairo.PDFSurface(self.output, w, h)

        cr = cairo.Context(s)
        cr.set_source_surface(self.surface, -(x0 + x1) + 1, -(y0 + y1) + 1)
        cr.paint()
        cr.show_page()
        if self.filetype == 'png':
            s.write_to_png(self.output)

        self.surface.flush()
        self.surface.finish()

        s.flush()
        s.finish()

