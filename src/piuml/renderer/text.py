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
Renderer text routines.
"""

import cairo
from gi.repository import Pango as pango
from gi.repository import PangoCairo

from math import atan2

from piuml.style import Pos

# Horizontal align.
ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = -1, 0, 1

# Vertical align.
ALIGN_TOP, ALIGN_MIDDLE, ALIGN_BOTTOM = -1, 0, 1

# Vertical line align (along the line from tail to head).
ALIGN_TAIL, ALIGN_HEAD = -1, 1

def text_pos_at_box(size, box, style, align, outside=False):
    """
    Calculate position of the text relative to containing box.

    :Parameters:
     size
        Width and height of text to be aligned.
     box
        Containing box.
     style
        Style of containing box (i.e. position and padding).
     align
        Horizontal and vertical alignment of text.
     outside
        If true the text is aligned outside the box.
    """
    w, h = size # size of the text
    width, height = box
    x0, y0 = style.pos
    pad = style.padding

    halign, valign = align

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
            y = -h - pad.top
        elif valign == ALIGN_MIDDLE:
            y = (height - h) / 2.0 + pad.top - pad.bottom
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
            y = (height - h) / 2.0 + pad.top - pad.bottom
        elif valign == ALIGN_BOTTOM:
            y = height - h - pad.bottom
        else:
            assert False
    return x + x0, y + y0


def text_pos_at_line(size, line, style, align, outside=False):
    """
    Calculate position of the text relative to specified line. Text is
    aligned using line style (i.e. padding) information. 

    The alignment is calculated from perspective of a person standing at
    the tail and looking towards the head

    - vertical alignment is from tail, through the middle, till the head
    - horizontal alignment can be at the left or right of the line

    :Parameters:
     size
        Width and height of text to be aligned.
     line
        Points defining a line.
     style
        Line style information like padding.
     align
        Horizontal and vertical alignment of text.
     outside
        If true the text is aligned outside the box.
    """
    width, height = size
    w2 = width / 2
    h2 = height / 2
    pad = style.padding
    halign, valign = align

    if valign == ALIGN_TAIL:
        p1, p2 = line[:2]
        x0, y0 = p1
    elif valign == ALIGN_HEAD:
        p1, p2 = line[-2:]
        x0, y0 = p2
    else: # ALIGN_MIDDLE
        p1, p2 = line_middle_segment(line)
        x0 = (p1.x + p2.x) / 2.0
        y0 = (p1.y + p2.y) / 2.0

    dx = p2.x - p1.x
    dy = p2.y - p1.y
    a = atan2(dy, dx)

    padh = (0, pad.right, pad.left)
    padv = (0, pad.bottom, pad.top)

    if abs(dx) > abs(dy): # horizontal line alignment
        ld = 1 if p1.x <= p2.x else 0
        sg = 1 if p1.x <= p2.x else -1
        op = (0.5, ld, not ld)
        gop = (1, -1, 1)
        #gop = (0, 0, 0)

        pv_op = (0, 1, -1)
        ph_op = (0, -1, 1)

        x0 -= op[valign] * width + sg * pv_op[valign] * padv[valign]
        y0 -= abs(1 - op[halign]) * height + sg * ph_op[halign] * padh[halign]

    else: # vertical line alignment
        ld = 1 if p1.y <= p2.y else 0
        sg = 1 if p1.y <= p2.y else -1
        op = (0.5, ld, not ld)

        p_op = (0, 1, -1)

        x0 -= op[halign] * width + sg * p_op[halign] * padh[halign] 
        y0 -= op[valign] * height + sg * p_op[valign] * padv[valign]

    return x0, y0


def line_middle_segment(edges):
    """
    Get positions of middle segment of a line represented by specified
    edges.
    """
    med = len(edges) // 2
    p1, p2 = edges[med - 1: med + 1]
    return p1, p2


def line_center(edges):
    """
    Get mid point and angle of middle segment of a line defined by
    specified edges.
    """
    p1, p2 = line_middle_segment(edges)
    pos = Pos((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    angle = atan2(p2.y - p1.y, p2.x - p1.x)
    return pos, angle


def pango_layout(cr, text):
    pl = PangoCairo.create_layout(cr._cr)
    pl.set_font_description(pango.FontDescription('sans 10'))
    _, attrs, pt, _ = pango.parse_markup(text, -1, '\0')
    pl.set_attributes(attrs)
    pl.set_text(pt, -1)
    return pl


def pango_size(layout):
    r = layout.get_pixel_extents()[1]
    return r.width, r.height


def draw_text(cr, shape, style, text,
        lalign=pango.Alignment.LEFT,
        pos=(0, 0),
        align=(0, -1),
        outside=False,
        align_f=text_pos_at_box):

    pl = pango_layout(cr, text)
    size = pango_size(pl)
    pl.set_alignment(lalign)

    x0, y0 = pos
    x, y = align_f(size, shape, style, align=align, outside=outside)

    cr.save()
    cr.move_to(x + x0, y + y0)
    PangoCairo.show_layout(cr._cr, pl)
    cr.restore()

    return size[1]


def text_size(cr, text):
    """
    Calculate total size of a multiline text.
    """
    pl = pango_layout(cr, text)
    return pango_size(pl)


# vim: sw=4:et:ai

