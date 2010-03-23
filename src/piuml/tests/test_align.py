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

from piuml.parser import Style, Pos, Area, Size
from piuml.renderer import draw_text, text_pos_at_line

class BoxAlignTestCase(unittest.TestCase):
    """
    Text alignment at a box tests.
    """
    def _draw(self, name, pad, outside=False):
        s = cairo.PDFSurface('src/piuml/tests/%s.pdf' % name, 400, 300)
        cr = cairo.Context(s)
        cr.rectangle(100, 100, 200, 100)
        cr.stroke()

        cr.save()
        cr.set_line_width(0.5)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)
        dd = 50 if outside else 2
        cr.move_to(100 - dd, 150)
        cr.line_to(300 + dd, 150)
        cr.move_to(200, 100 - dd)
        cr.line_to(200, 200 + dd)
        cr.stroke()
        cr.restore()

        if any(pad):
            cr.save()
            cr.set_line_width(0.75)
            cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
            sign = -1 if outside else 1
            cr.rectangle(100 + sign * pad[3],
                    100 + sign * pad[0],
                    200 - sign * (pad[1] + pad[3]),
                    100 - sign * (pad[0] + pad[2]))
            cr.stroke()
            cr.restore()

        style = Style()
        style.size = Size(200, 100)
        style.pos = Pos(100, 100)
        style.padding = Area(*pad)

        dt = partial(draw_text, cr, style.size, style, outside=outside)
        dt('(CENTRAL)', align=(0, 0))
        dt('(TOP)', align=(0, -1))
        dt('(BOTTOM)', align=(0, 1))
        dt('(LEFT)', align=(-1, 0))
        dt('(RIGHT)', align=(1, 0))
        dt('(LEFTTOP)', align=(-1, -1))
        dt('(RIGHTTOP)', align=(1, -1))
        dt('(LBOTTOM)', align=(-1, 1))
        dt('(RBOTTOM)', align=(1, 1))

        s.flush()
        s.finish()


    def test_inner_align(self):
        """Test inner box align
        """
        self._draw('box_align_i', (0, 0, 0, 0))
        self._draw('box_align_ip', (20, 10, 20, 10))

    def test_outer_align(self):
        """Test outer box align
        """
        self._draw('box_align_o', (0, 0, 0, 0), True)
        self._draw('box_align_op', (20, 10, 20, 10), True)
        


class LineAlignTestCase(unittest.TestCase):
    """
    Text alignment at a line tests.
    """
    def _draw(self, name, line, pad):
        s = cairo.PDFSurface('src/piuml/tests/%s.pdf' % name, 400, 300)
        cr = cairo.Context(s)

        cr.move_to(*line[0])
        cr.arc(line[0][0], line[0][1], 1.0, 0.0, 2.0 * pi)
        for p1, p2 in zip(line[:-1], line[1:]):
            cr.move_to(*p1)
            cr.line_to(*p2)
            cr.arc(p2[0], p2[1], 1.0, 0.0, 2.0 * pi)
        cr.stroke()

        if any(pad):
            cr.save()
            cr.set_line_width(0.75)
            cr.set_source_rgba(1.0, 0.0, 0.0, 0.5)
            p1 = line[0]
            p2 = line[-1]
            cr.rectangle(p1[0] + pad[3],
                    p1[1] + pad[0],
                    p2[0] - p1[0] - (pad[1] + pad[3]),
                    p2[1] - p1[1] - (pad[0] + pad[2]))
            cr.stroke()
            cr.restore()

        style = Style()
        style.size = Size(0, 0)
        style.pos = Pos(0, 0)
        style.padding = Area(*pad)

        dt = partial(draw_text, cr, line, style, align_f=text_pos_at_line)
        dt('(TOP)', align=(0, -1))
        dt('(BOTTOM)', align=(0, 1))
        dt('(LEFT TOP)', align=(-1, -1))
        dt('(RIGHT TOP)', align=(1, -1))
        dt('(L-BOTTOM)', align=(-1, 1))
        dt('(R-BOTTOM)', align=(1, 1))

        s.flush()
        s.finish()


    def test_halign(self):
        """Test text at horizontal line alignment
        """
        line = tuple((x, 150) for x in (100, 150, 250, 300))
        self._draw('line_align_h', line, (0, 0, 0, 0))
        self._draw('line_align_hp', line, (10, 5, 10, 5))


    def test_valign(self):
        """Test text at vertical line alignment
        """
        line = tuple((200, y) for y in (100, 125, 175, 200))
        self._draw('line_align_v', line, (0, 0, 0, 0))
        self._draw('line_align_vp', line, (10, 5, 10, 5))


    def test_ahalign(self):
        """Test text at almost horizontal line alignment
        """
        line = tuple(zip((100, 150, 250, 300), (150, 140, 160, 150)))
        self._draw('line_align_ah', line, (0, 0, 0, 0))
        self._draw('line_align_ahp', line, (10, 5, 10, 5))


    def test_avalign(self):
        """Test text at almost vertical line alignment
        """
        line = tuple(zip((200, 190, 210, 200), (100, 125, 175, 200)))
        self._draw('line_align_av', line, (0, 0, 0, 0))
        self._draw('line_align_avp', line, (10, 5, 10, 5))


# vim: sw=4:et:ai
