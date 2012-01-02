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
Text alignment tests.
"""

from functools import partial
from math import pi
import cairo
import unittest

from piuml.style import Style, Pos, Area, Size
from piuml.renderer.cr import CairoBBContext
from piuml.renderer.text import draw_text, text_pos_at_line, ALIGN_CENTER, \
    ALIGN_TOP, ALIGN_BOTTOM, ALIGN_TAIL, ALIGN_HEAD, ALIGN_LEFT, \
    ALIGN_RIGHT, ALIGN_MIDDLE

surface = cairo.PDFSurface('src/piuml/tests/align.pdf', 600, 300)
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
        p1 = line[0]
        p2 = line[-1]
        if any(pad):
            cr.rectangle(p1.x + pad[3],
                    p1.y + pad[0],
                    abs(p2.x - p1.x) - (pad[1] + pad[3]),
                    abs(p2.y - p1.y) - (pad[0] + pad[2]))
        cr.stroke()
        cr.move_to(p1.x, p1.y)
        cr.line_to(p2.x, p2.y)
        cr.stroke()
        cr.restore()

        style = Style()
        style.size = Size(0, 0)
        style.pos = Pos(0, 0)
        style.padding = Area(*pad)

        dt = partial(draw_text, cr, line, style, align_f=text_pos_at_line)
        dt('(LEFT TAIL)', align=(ALIGN_LEFT, ALIGN_TAIL))
        dt('(RIGHT TAIL)', align=(ALIGN_RIGHT, ALIGN_TAIL))
        dt('(LEFT HEAD)', align=(ALIGN_LEFT, ALIGN_HEAD))
        dt('(RIGHT HEAD)', align=(ALIGN_RIGHT, ALIGN_HEAD))
        dt('(LEFT)', align=(ALIGN_LEFT, ALIGN_MIDDLE))
        dt('(RIGHT)', align=(ALIGN_RIGHT, ALIGN_MIDDLE))

        cr.show_page()


    def test_halign(self):
        """
        Test text at horizontal line alignment
        """
        line = tuple(Pos(x, 150) for x in (100, 250, 350, 500))
        rline = tuple(reversed(line))
        self._draw('line_align_h', line, (0, 0, 0, 0))
        self._draw('line_align_h', rline, (0, 0, 0, 0))
        self._draw('line_align_hp', line, (10, 5, 10, 5))
        self._draw('line_align_hp', rline, (10, 5, 10, 5))


    def test_valign(self):
        """
        Test text at vertical line alignment
        """
        line = tuple(Pos(300, y) for y in (100, 125, 165, 200))
        rline = tuple(reversed(line))
        self._draw('line_align_v', line, (0, 0, 0, 0))
        self._draw('line_align_v', rline, (0, 0, 0, 0))
        self._draw('line_align_vp', line, (10, 5, 10, 5))
        self._draw('line_align_vp', rline, (10, 5, 10, 5))


    def test_ahalign(self):
        """
        Test text at almost horizontal line alignment
        """
        line = tuple(Pos(x, y) for x, y in zip((100, 250, 400, 500), (150, 140, 160, 150)))
        rline = tuple(reversed(line))
        self._draw('line_align_ah', line, (0, 0, 0, 0))
        self._draw('line_align_ah', rline, (0, 0, 0, 0))
        self._draw('line_align_ahp', line, (10, 5, 10, 5))
        self._draw('line_align_ahp', rline, (10, 5, 10, 5))

        line = tuple(Pos(x, y) for x, y in zip((100, 250, 400, 500), (150, 160, 140, 150)))
        rline = tuple(reversed(line))
        self._draw('line_align_ah', line, (0, 0, 0, 0))
        self._draw('line_align_ah', rline, (0, 0, 0, 0))
        self._draw('line_align_ahp', line, (10, 5, 10, 5))
        self._draw('line_align_ahp', rline, (10, 5, 10, 5))


    def test_avalign(self):
        """
        Test text at almost vertical line alignment
        """
        line = tuple(Pos(x, y) for x, y in zip((200, 190, 210, 200), (100, 125, 175, 200)))
        rline = tuple(reversed(line))
        self._draw('line_align_av', line, (0, 0, 0, 0))
        self._draw('line_align_av', rline, (0, 0, 0, 0))
        self._draw('line_align_avp', line, (10, 5, 10, 5))
        self._draw('line_align_avp', rline, (10, 5, 10, 5))

        line = tuple(Pos(x, y) for x, y in zip((200, 210, 190, 200), (100, 125, 175, 200)))
        self._draw('line_align_av', line, (0, 0, 0, 0))
        self._draw('line_align_avp', line, (10, 5, 10, 5))


# vim: sw=4:et:ai
