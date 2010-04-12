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
piUML rendering tests.
"""

from piuml.renderer.util import st_fmt

import unittest

class StereotypeTestCase(unittest.TestCase):
    """
    Stereotype rendering tests.
    """
    def test_single(self):
        """Test single stereotype rendering
        """
        self.assertEquals(u'<<t1>>', st_fmt(['t1']))


    def test_multiple(self):
        """Test multiple stereotype rendering
        """
        self.assertEquals(u'<<t1, t2, t3>>', st_fmt(['t1', 't2', 't3']))


    def test_keywords(self):
        """Test stereotypes rendering with keywords
        """
        self.assertEquals(u'<<interface>> <<t1, t2, t3>>', st_fmt(['t1', 'interface', 't2', 't3']))

# vim: sw=4:et:ai
