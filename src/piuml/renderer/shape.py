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
piUML renderer shapes.
"""

from math import pi

def draw_box3d(cr, pos, size):
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
    x = pos.x + tab[0]
    y = pos.y - tab[1]
    cr.rectangle(pos.x, pos.y, size.width, size.height)
    cr.move_to(pos.x, pos.y)
    cr.line_to(pos.x, y)
    cr.line_to(x, y)
    cr.line_to(x, pos.y)
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

# vim: sw=4:et:ai

