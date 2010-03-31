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
MetaUML/Metapost based layout.
"""

from piuml.layout import PreLayout

class MLayout(PreLayout):
    def size(self, node):
        ns = node.style

    def within(self, parent, node):
        ns = node.style
        ps = parent.style

    def top(self, *nodes):
        pass

    def bottom(self, *nodes):
        pass

    def left(self, *nodes):
        pass

    def right(self, *nodes):
        pass

    def center(self, *nodes):
        pass

    def middle(self, *nodes):
        pass

    def hspan(self, *nodes):
        pass

    def vspan(self, *nodes):
        pass

# vim: sw=4:et:ai

