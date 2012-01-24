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
piUML is UML diagram generator.

piUML provides simple and powerful language, which allows to easily write
complex diagrams in UML notation. Diagram information defined with piUML
language is analyzed and diagram is rendered into PDF file using automatic
layout.
"""

from piuml.parser import parse
from piuml.layout import Layout, Router
from piuml.renderer import Renderer

__version__ = '0.1.0'

def generate(f, fout, filetype='pdf'):
    """
    Generate UML diagram into output file.

    :Parameters:
     f
        File containing UML diagram description in piUML language.
     fout
        Output of file name.
     filetype
        Type of a file: pdf, svg or mp.
    """
    graph = Layout()
    renderer = Renderer()
    router = Router()

    renderer.filetype = filetype
    renderer.output = fout

    ast = parse(f)
    renderer.measure(ast)
    graph.layout(ast)
    router.route(ast)
    renderer.render(ast)


# vim: sw=4:et:ai
