"""
piUML for Sphinx extension.
"""

import os.path
from docutils import nodes

from sphinx.errors import SphinxError
from docutils.parsers.rst.directives.images import Figure

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
        fin = uri + '.txt'
        fname = os.path.basename(uri) + '.svg'
        fout = os.path.join(self.app.builder.outdir, '_images', fname)
        
        with open(fin) as f:
            generate(f, fout, 'svg')
            img['uri'] = fname
        return data


def setup(app):
    UMLDiagram.app = app
    app.add_directive('uml-diagram', UMLDiagram)

# vim: sw=4:et:ai
