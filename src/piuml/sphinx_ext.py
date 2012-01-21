"""
piUML for Sphinx extension.
"""

import os.path
from docutils import nodes
from docutils.parsers.rst.directives.images import Figure

from sphinx.errors import SphinxError
from sphinx.util.osutil import ensuredir

from piuml import generate

class UMLDiagramError(SphinxError):
    category = 'UMLDiagram error'


class uml_diagram(nodes.image):
    pass


class UMLDiagram(Figure):
    """
    UML diagram directive.
    """
    def run(self):
        #if not dotcode.strip():
        #    return [self.state_machine.reporter.warning(
        #        'Ignoring "uml_diagram" directive without content.',
        #        line=self.lineno)]
        data = Figure.run(self)
        img = data[0][0]

        uri = img['uri']
        fin = uri + '.pml'
        fname = os.path.basename(uri) + '.svg'
        _, tdir = self.app.env.relfn2path('')
        fout = os.path.join(tdir, fname)
        
        with open(fin) as f:
            generate(f, fout, 'svg')
            img['uri'] = fname
        return data


def setup(app):
    UMLDiagram.app = app
    app.add_directive('uml-diagram', UMLDiagram)

# vim: sw=4:et:ai
