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
Text alignment tests.
"""

from functools import partial
from math import pi
import cairo
import unittest

from piuml.style import Style, Pos, Area, Size
from piuml.renderer.cr import CairoBBContext
from piuml.renderer.text import draw_text, text_pos_at_line, \
    line_single_text_hint, line_middle_segment, ALIGN_CENTER, ALIGN_MIDDLE, \
    ALIGN_TOP, ALIGN_BOTTOM, \
    ALIGN_TAIL, ALIGN_HEAD, \
    ALIGN_LEFT, ALIGN_RIGHT

surface = cairo.PDFSurface('src/piuml/tests/align.pdf', 600, 600)
cr = CairoBBContext(cairo.Context(surface))

class BoxAlignTestCase(unittest.TestCase):
    """
    Text alignment at a box tests.
    """
    def _draw(self, name, pad, outside=False):
        cr.rectangle(100, 100, 400, 100)
        cr.stroke()

        cr.save()
        cr.set_line_width(0.5)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
        dd = 50 if outside else 2
        cr.move_to(100 - dd, 150)
        cr.line_to(500 + dd, 150)
        cr.move_to(300, 100 - dd)
        cr.line_to(300, 200 + dd)
        cr.stroke()
        cr.restore()

        if any(pad):
            cr.save()
            cr.set_line_width(0.75)
            cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
            sign = -1 if outside else 1
            cr.rectangle(100 + sign * pad[3],
                    100 + sign * pad[0],
                    400 - sign * (pad[1] + pad[3]),
                    100 - sign * (pad[0] + pad[2]))
            cr.stroke()
            cr.restore()

        style = Style()
        style.size = Size(400, 100)
        style.pos = Pos(100, 100)
        style.padding = Area(*pad)

        dt = partial(draw_text, cr, style.size, style, outside=outside)
        dt('(CENTRAL)', align=(0, 0))
        dt('(TOP)', align=(0, -1))
        dt('(BOTTOM)', align=(0, 1))
        dt('(LEFT)', align=(-1, 0))
        dt('(RIGHT)', align=(1, 0))
        dt('(L-TOP)', align=(-1, -1))
        dt('(R-TOP)', align=(1, -1))
        dt('(L-BOTTOM)', align=(-1, 1))
        dt('(R-BOTTOM)', align=(1, 1))

        cr.show_page()


    def test_inner_align(self):
        """
        Test inner box align
        """
        self._draw('box_align_i', (0, 0, 0, 0))
        self._draw('box_align_ip', (20, 10, 20, 10))

    def test_outer_align(self):
        """
        Test outer box align
        """
        self._draw('box_align_o', (0, 0, 0, 0), True)
        self._draw('box_align_op', (20, 10, 20, 10), True)
        


class LineAlignTestCase(unittest.TestCase):
    """
    Text alignment at a line tests.
    """
    def _draw(self, name, line, pad):
        cr.rectangle(line[0].x - 3, line[0].y - 3, 6, 6)
        for p1, p2 in zip(line[:-1], line[1:]):
            cr.move_to(*p1)
            cr.line_to(*p2)
            cr.arc(p2.x, p2.y, 1, 0.0, 2.0 * pi)
        cr.stroke()

        cr.save()
        cr.set_line_width(0.75)
        cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
        p1, p2 = line_middle_segment(line)
        x0 = p1.x + (p2.x - p1.x) / 2
        y0 = p1.y + (p2.y - p1.y) / 2
        cr.move_to(x0 - 40, y0)
        cr.line_to(x0 + 40, y0)
        cr.move_to(x0, y0 - 40)
        cr.line_to(x0, y0 + 40)
        cr.stroke()
        cr.restore()

        style = Style()
        style.size = Size(0, 0)
        style.pos = Pos(0, 0)
        style.padding = pad

        def dt(text, valign):
            lt = '(L {})'.format(text)
            rt = '(R {})'.format(text)
            draw_text(cr, line, style, lt, align=(ALIGN_LEFT, valign), align_f=text_pos_at_line)
            draw_text(cr, line, style, rt, align=(ALIGN_RIGHT, valign), align_f=text_pos_at_line)

        dt('TAIL', ALIGN_TAIL)
        dt('HEAD', ALIGN_HEAD)
        dt('MID', ALIGN_MIDDLE)

        cr.show_page()


    def test_align(self):
        """
        Test text alignment at a line
        """
        p0 = Pos(300, 300)

        pad = Area(0, 0, 0, 0)
        for x in range(570, 30, -30):
            self._draw('a', (p0, Pos(x, 570)), pad)
        for y in range(570, 30, -30):
            self._draw('a', (p0, Pos(30, y)), pad)
        for x in range(30, 600, 30):
            self._draw('a', (p0, Pos(x, 30)), pad)
        for y in range(30, 600, 30):
            self._draw('a', (p0, Pos(570, y)), pad)

        pad = Area(10, 5, 10, 5)
        for x in range(570, 30, -30):
            self._draw('a', (p0, Pos(x, 570)), pad)
        for y in range(570, 30, -30):
            self._draw('a', (p0, Pos(30, y)), pad)
        for x in range(30, 600, 30):
            self._draw('a', (p0, Pos(x, 30)), pad)
        for y in range(30, 600, 30):
            self._draw('a', (p0, Pos(570, y)), pad)


# vim: sw=4:et:ai
