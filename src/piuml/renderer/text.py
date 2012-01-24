#
# piUML - UML diagram generator.
#
# Copyright (C) 2010 - 2012 by Artur Wroblewski <wrobell@pld-linux.org>
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

from math import atan2, pi, sin, cos

# Horizontal align.
ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = -1, 0, 1

# Vertical align.
ALIGN_TOP, ALIGN_MIDDLE, ALIGN_BOTTOM = -1, 0, 1

# Vertical line align (along the line from tail to head).
ALIGN_TAIL, ALIGN_HEAD = -1, 1

EPSILON = 1e-6

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

    TODO

    - tail and head alignment at the line needs improvement
    - consider line attached to vertical or horizontal edge of a box
    """
    width, height = size
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

    kx = p1.x > p2.x
    ky = p1.y > p2.y

    xml, xmr = 0, 0
    yml, ymr = 0, 0
    if abs(dx) < EPSILON:
        # fixme: to get rid of x00/y00 investigate 
        #   kx = cmp(p1.x, p1.y) 
        # and that
        #   ~(-2, -1, 0, 1) = (1, 0, -1, -2)
        yml += height / 2
        ymr += -height / 2
    elif abs(dy) < EPSILON:
        xml += -width / 2
        xmr += width / 2

    # (-2, -1, 0, 1) = ~(1, 0, -1, -2)
    ym = (not kx ^ ky) - (not ky) - 2 * (kx and ky)

    if abs(dx) > abs(dy): # horizontal
        xop = ((),
               (-(not ky), -(not kx), -kx), # right: middle, head, tail
               (-ky, -(not kx), -kx),) # left: middle, head, tail
        yop = ((),
               (ym, ym, ym), # right: middle, head, tail
               (~ym, ~ym, ~ym),) # left: middle, head, tail
    else: # vertical
        xm = -ky
        xop = ((),
               (~xm, ~xm, ~xm), # right: middle, head, tail
               (xm, xm, xm),) # left: middle, head, tail
        yop = ((),
               (ym, ~xm, xm), # right: middle, head, tail
               (~ym, ~xm, xm),) # left: middle, head, tail
    mxop = ((),
           (xmr, 0, 0), # right: middle, head, tail
           (xml, 0, 0)) # left: middle, head, tail
    myop = ((),
           (ymr, 0, 0), # right: middle, head, tail
           (yml, 0, 0),) # left: middle, head, tail

    # fixme: simplify with vector operations, i.e.
    #   -sin(a) * ((pad.right,) * 3) + cos(a) * (0, -pad.top, pad.bottom)
    #   sin(a) * ((pad.left,) * 3) + cos(a) * (0, -pad.top, pad.bottom)
    #   cos(a) * ((pad.right,) * 3) + sin(a) * (0, -pad.top, pad.bottom)
    #   -cos(a) * ((pad.left,) * 3) + sin(a) * (0, -pad.top, pad.bottom)
    pxop = ((),
           (-pad.right * sin(a), -pad.right * sin(a) - pad.top * cos(a), -pad.right * sin(a) + pad.bottom * cos(a)), # right: middle, head, tail
           (pad.left * sin(a), pad.left * sin(a) - pad.top * cos(a),  pad.left * sin(a) + pad.bottom * cos(a)),) # left: middle, head, tail
    pyop = ((),
           (pad.right * cos(a), pad.right * cos(a) - pad.top * sin(a), pad.right * cos(a) + pad.bottom * sin(a)), # right: middle, head, tail
           (-pad.left * cos(a), -pad.left * cos(a) - pad.top * sin(a), -pad.left * cos(a) + pad.bottom * sin(a)),) # left: middle, head, tail

    x0 += width * xop[halign][valign] + mxop[halign][valign] + pxop[halign][valign]
    y0 += height * yop[halign][valign] + myop[halign][valign] + pyop[halign][valign]

    return x0, y0


def line_single_text_hint(line, style, align):
    halign, valign = align

    if valign == ALIGN_TAIL:
        p1, p2 = line[:2]
    elif valign == ALIGN_HEAD:
        p1, p2 = line[-2:]
    else: # ALIGN_MIDDLE
        p1, p2 = line_middle_segment(line)

    dx = p2.x - p1.x
    dy = p2.y - p1.y

    if abs(dx) < EPSILON or abs(dy) < EPSILON:
        da = 0
    else:
        da = abs(dy / dx)
   
    # <0, 30>, <150, 180>, <-180, -150>, <-30, 0>
    return da > 0.6


def line_middle_segment(edges):
    """
    Get positions of middle segment of a line represented by specified
    edges.
    """
    med = len(edges) // 2
    p1, p2 = edges[med - 1: med + 1]
    return p1, p2


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
    w, h = size = pango_size(pl)
    pl.set_alignment(lalign)

    x, y = align_f(size, shape, style, align=align, outside=outside)
    x += pos[0]
    y += pos[1]

    cr.save()
    cr.move_to(x, y)

    x1, y1 = cr.user_to_device(x, y)
    x2, y2 = cr.user_to_device(x + w, y + h)
    PangoCairo.show_layout(cr._cr, pl)
    cr._update_bbox((x1, y1, x2, y2))

    cr.restore()

    return size[1]


def text_size(cr, text):
    """
    Calculate total size of a multiline text.
    """
    pl = pango_layout(cr, text)
    return pango_size(pl)


# vim: sw=4:et:ai

