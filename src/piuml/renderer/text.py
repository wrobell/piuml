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

    fixme: works for straight vertical and horizontal lines
    """
    EPSILON = 1e-6

    width, height = size
    pad = style.padding
    halign, valign = align

    if halign == ALIGN_LEFT:
        p1, p2 = line[:2]
    elif halign == ALIGN_RIGHT:
        p1, p2 = line[-2:]
    else: # ALIGN_CENTER
        p1, p2 = line_middle_segment(line)

    x0 = (p1.x + p2.x) / 2.0
    y0 = (p1.y + p2.y) / 2.0
    dx = p2.x - p1.x
    dy = p2.y - p1.y

    if abs(dx) < EPSILON:
        d1 = -1.0
        d2 = 1.0
    elif abs(dy) < EPSILON:
        d1 = 0.0
        d2 = 0.0
    else:
        d1 = dy / dx
        d2 = abs(d1)

    # move to center and move by delta depending on line angle
    if d2 < 0.5774: # <0, 30>, <150, 180>, <-180, -150>, <-30, 0>
        # horizontal mode
        w2 = width / 2.0
        hint = w2 * d2

        if halign == ALIGN_LEFT:
            x = p1.x + pad.left
        elif halign == ALIGN_RIGHT:
            x = p2.x - width - pad.right
        else:
            x = x0 - w2

        if valign == ALIGN_TOP:
            y = y0 - pad.top - hint - height
        else:
            y = y0 + pad.bottom + hint
    else: # much better in case of vertical lines

        # hint tuples to move text depending on quadrant
        WIDTH_HINT = (0, 0, -1)    # width hint tuple
        R_WIDTH_HINT = (-1, -1, 0)    # width hint tuple
        PADDING_HINT = (1, 1, -1)  # padding hint tuple

        # determine quadrant, we are interested in 1 or 3 and 2 or 4
        # see hint tuples below
        h2 = height / 2.0
        q = cmp(d1, 0)
        if abs(dx) < EPSILON:
            hint = 0
        else:
            hint = h2 / d2

        if halign == ALIGN_LEFT:
            y = p1.y + pad.top
        elif halign == ALIGN_RIGHT:
            y = p2.y - pad.bottom - height
        else:
            y = y0 - h2

        if valign == ALIGN_TOP:
            x = p1.x - width - pad.left
        elif valign == ALIGN_BOTTOM:
            x = p1.x + pad.right + hint
        else:
            assert False

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
    pos = Pos((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    angle = atan2(p2.y - p1.y, p2.x - p1.x)
    return pos, angle


def pango_layout(cr, text):
    l = PangoCairo.create_layout(cr._cr)
    l.set_font_description(pango.FontDescription('sans 10'))
    _, attrs, _, _ = pango.parse_markup(text, -1, '\0')
    l.set_attributes(attrs)
    l.set_text(text, -1)
    return l


def pango_size(layout):
    r = layout.get_pixel_extents()[1]
    return r.width, r.height


def draw_text(cr, shape, style, text,
        lalign=pango.Alignment.LEFT,
        pos=(0, 0),
        align=(0, -1),
        outside=False,
        align_f=text_pos_at_box):

    l = pango_layout(cr, text)
    size = pango_size(l)
    l.set_alignment(lalign)

    x0, y0 = pos
    x, y = align_f(size, shape, style, align=align, outside=outside)

    cr.save()
    cr.move_to(x + x0, y + y0)
    l.show(l)
    cr.restore()

    return size[1]


def text_size(cr, text):
    """
    Calculate total size of a multiline text.
    """
    l = pango_layout(cr, text)
    return pango_size(l)


# vim: sw=4:et:ai

