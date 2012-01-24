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
piUML renderer shapes.
"""

from math import pi

def draw_box3d(cr, pos, size):
    """
    Draw 3D box.

    :Parameters:
     pos
        Position of the box.
     size
        Width and height of the box.
    """
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


def draw_tabbed_box(cr, pos, size, tab=(50, 20)):
    """
    Draw tabbed box.

    :Parameters:
     cr
        Cairo context.
     pos
        Position of the box.
     size
        Size of the box.
     tab
        Size of the tab.
    """
    y = pos.y + tab[1]
    cr.rectangle(pos.x, y, size.width, size.height - tab[1])
    cr.move_to(pos.x, y)
    cr.rel_line_to(0, -tab[1])
    cr.rel_line_to(tab[0], 0)
    cr.rel_line_to(0, tab[1])
    cr.stroke()


def draw_ellipse(cr, pos, r1, r2):
    """
    Draw ellipse.
    
    :Parameters:
     cr
        Cairo context.
     pos
        Center of the ellipse.
     r1
        Ellipse horizontal radius.
     r2
        Ellipse vertical radius.
    """
    cr.save()
    cr.translate(*pos)
    cr.scale(r1, r2)
    cr.move_to(1.0, 0.0)
    cr.arc(0.0, 0.0, 1.0, 0.0, 2.0 * pi)
    cr.restore()


def draw_note(cr, pos, size, ear=15):
    """
    Draw note shape.

    Parameters:
     cr
        Cairo context.
     pos
        Position of note rectangle.
     size
        Width and height of the note rectangle.
     ear
        Length of "ear" of the line.
    """
    width, height = size
    x, y = pos
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


def draw_human(cr, pos, size):
    """
    Draw human figure.

    :Parameters:
     pos
        Left, top position of the figure.
     size
        Width and height of the figure.
    """
    head = 11
    arm  = 19
    neck = 10
    body = 20
    width, height = size
    x0, y0 = pos

    fx = width / (arm * 2);
    fy = height / (head + neck + body + arm)

    x = x0 + arm * fx
    y = y0 + (head / 2.0) * fy
    cy = head * fy

    cr.move_to(x + head * fy / 2.0, y)
    cr.arc(x, y, head * fy / 2.0, 0, 2 * pi)

    cr.move_to(x, y + cy / 2)
    cr.line_to(x0 + arm * fx, y0 + (head + neck + body) * fy)

    cr.move_to(x0, y0 + (head + neck) * fy)
    cr.line_to(x0 + arm * 2 * fx, y0 + (head + neck) * fy)

    cr.move_to(x0, y0 + (head + neck + body + arm) * fy)
    cr.line_to(x0 + arm * fx, y0 + (head + neck + body) * fy)
    cr.line_to(x0 + arm * 2 * fx, y0 + (head + neck + body + arm) * fy)
    cr.stroke()


def draw_component(cr, pos, size):
    """
    Draw component shape.

    :Parameters:
     cr
        Cairo context.
     pos
        Left, top position of the component.
     size
        Width and height of the component.
    """
    w, h = size
    BAR_WIDTH = 2.0 / 3.0 * w
    BAR_HEIGHT =  h / 5.0
    BAR_PADDING = h / 5.0

    ix, iy = pos

    cr.save()
    cr.set_line_width(0.8)
    cr.rectangle(ix, iy, w, h)
    cr.stroke()

    bx = ix - BAR_PADDING
    bar_upper_y = iy + BAR_PADDING
    bar_lower_y = iy + BAR_PADDING * 3

    color = cr.get_source()
    cr.rectangle(bx, bar_lower_y, BAR_WIDTH, BAR_HEIGHT)
    cr.set_source_rgb(1,1,1) # white
    cr.fill_preserve()
    cr.set_source(color)
    cr.stroke()

    cr.rectangle(bx, bar_upper_y, BAR_WIDTH, BAR_HEIGHT)
    cr.set_source_rgb(1,1,1) # white
    cr.fill_preserve()
    cr.set_source(color)
    cr.stroke()
    cr.restore()


def draw_artifact(cr, pos, size):
    """
    Draw artifact shape.

    :Parameters:
     cr
        Cairo context.
     pos
        Left, top position of the artifact.
     size
        Width and height of the artifact.
    """
    cr.save()
    w, h = size
    ix, iy = pos
    ear = 5

    cr.set_line_width(0.8)
    cr.move_to(ix + w - ear, iy)
    cr.line_to(ix + w - ear, iy + ear)
    cr.line_to(ix + w, iy + ear)
    cr.line_to(ix + w - ear, iy)
    cr.line_to(ix, iy)
    cr.line_to(ix, iy + h)
    cr.line_to(ix + w, iy + h)
    cr.line_to(ix + w, iy + ear)

    cr.stroke()
    cr.restore()

# vim: sw=4:et:ai
