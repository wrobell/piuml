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
piUML renderer routines for lines.
"""

import cairo
from math import atan2

def draw_line(cr, edges, draw_tail=None, draw_head=None, dash=None):
    if draw_tail is None:
        draw_tail = draw_tail_none
    if draw_head is None:
        draw_head = draw_head_none

    p0, p1 = edges[:2]
    t_angle = atan2(p1[1] - p0[1], p1[0] - p0[0])
    p1, p0 = edges[-2:]
    h_angle = atan2(p1[1] - p0[1], p1[0] - p0[0])

    cr.save()
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    draw_line_end(cr, edges[0], t_angle, draw_tail)
    if dash is not None:
        cr.set_dash(dash, 0)
    for x, y in edges[1:-1]:
        cr.line_to(x, y)
    draw_line_end(cr, edges[-1], h_angle, draw_head)
    cr.stroke()
    cr.restore()


def draw_line_end(cr, pos, angle, draw):
    cr.save()
    cr.translate(*pos)
    cr.rotate(angle)
    draw(cr)
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


def draw_head_arrow(cr, fill=False):
    """
    Draw a normal arrow to indicate association end navigability at
    association head.
    """
    dash = cr.get_dash()

    # finish the line
    cr.line_to(0, 0)
    cr.stroke()

    # draw the arrow
    cr.set_dash((), 0)
    cr.move_to(15, -6)
    cr.line_to(0, 0)
    cr.line_to(15, 6)
    if fill:
        cr.close_path()
        cr.fill_preserve()
    cr.stroke()
    cr.set_dash(*dash)


def draw_tail_arrow(cr, fill=False):
    """
    Draw a normal arrow to indicate association end navigability at
    association tail.
    """
    cr.move_to(15, -6)
    cr.line_to(0, 0)
    cr.line_to(15, 6)
    if fill:
        cr.close_path()
        cr.fill_preserve()
    cr.stroke()
    cr.move_to(0, 0)


def draw_head_triangle(cr):
    dash = cr.get_dash()
    cr.line_to(15, 0)
    cr.stroke()

    # draw the triangle
    cr.set_dash((), 0)
    cr.move_to(0, 0)
    cr.line_to(15, -10)
    cr.line_to(15, 10)
    cr.close_path()
    cr.stroke()
    cr.set_dash(*dash)


def draw_tail_triangle(cr):
    cr.move_to(0, 0)
    cr.line_to(15, -10)
    cr.line_to(15, 10)
    cr.close_path()
    cr.stroke()
    cr.move_to(15, 0)


# vim: sw=4:et:ai

