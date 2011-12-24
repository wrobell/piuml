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
Style information of rendered UML diagram items.
"""

from piuml.data import Element, Relationship

import logging
log = logging.getLogger('piuml.renderer.style')


class Pos(object):
    """
    Position of diagram item.
    """
    __slots__ = 'x', 'y'

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

    def __str__(self):
        return '(%s, %s)' % (self.x, self.y)

    def __eq__(self, p):
        return self.x == p.x and self.y == p.y

    def __repr__(self):
        return 'Pos({},{})'.format(self.x, self.y)



class Size(object):
    """
    Width and height of diagram item.
    """
    __slots__ = 'width', 'height'

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __iter__(self):
        return iter((self.width, self.height))

    def __str__(self):
        return '%s, %s' % (self.width, self.height)


class Area(object):
    """
    Area related to diagram item like item margins or padding information.
    """
    __slots__ = 'top', 'right', 'bottom', 'left'

    def __init__(self, top, right, bottom, left):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def __iter__(self):
        return iter((self.top, self.right, self.bottom, self.left))



class Style(object):
    """
    Base style class for diagram items.

    :Attributes:
     margin
        Item margins.
     padding
        Item padding.
    """
    def __init__(self):
        self.margin = Area(10, 10, 10, 10)
        self.padding = Area(5, 10, 5, 10)



class BoxStyle(Style):
    """
    Box style information.

    Rectangle of the box is defined by its position and size.

    Box has compartments. There is at least one compartment containing
    information like UML stereotypes, name of UML named element or simply
    other boxes.

    Box may have an icon, which is displayed in top right corner of the
    box, i.e. UML artifact or UML component icon.

    :Attributes:
     pos
        Box position.
     size
        Current size of the box.
     min_size
        Minimum size of the box.
     compartment
        Height of each compartment.
     icon_size
        Icon size.
    """
    def __init__(self):
        """
        Create box style information.
        """
        super(BoxStyle, self).__init__()

        # box specific
        self.pos = Pos(0, 0)
        self.size = Size(80, 40)
        self.icon_size = Size(0, 0)
        self.min_size = Size(80, 40)
        self.compartment = [0]



class LineStyle(Style):
    """
    Line style.

    :Attributes:
     edges
        List of line points. 
    """
    def __init__(self):
        """
        Create line style information.
        """
        super(LineStyle, self).__init__()
        self.min_length = 100
        self.edges = (Pos(0, 0), Pos(0, 0))



class StyleDescriptor(object):
    """
    Injects style information into UML diagram items.

    :Attributes:
     cls
        Class for a diagram item.
     data
        Style information per UML diagram item.
    """
    def __init__(self, cls):
        super(StyleDescriptor, self).__init__()
        self.cls = cls
        self.data = {}

    def __get__(self, obj, cls=None):
        """
        Get style information for an object.
        """
        if obj not in self.data:
            self.data[obj] = self.cls()
        return self.data[obj]


Element.style = StyleDescriptor(BoxStyle)
Relationship.style = StyleDescriptor(LineStyle)

# vim: sw=4:et:ai
