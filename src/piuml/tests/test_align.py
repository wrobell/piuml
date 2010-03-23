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
import cairo
import unittest

from piuml.parser import Style, Pos, Area, Size
from piuml.renderer import draw_text

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
        self._draw('align_i', (0, 0, 0, 0))
        self._draw('align_ip', (20, 10, 20, 10))

    def test_outer_align(self):
        """Test outer box align
        """
        self._draw('align_o', (0, 0, 0, 0), True)
        self._draw('align_op', (20, 10, 20, 10), True)


# vim: sw=4:et:ai
