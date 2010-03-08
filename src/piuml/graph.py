from spark import GenericASTTraversal

from piuml.parser import Pos, Size

class ToGVConverter(GenericASTTraversal):
    def __init__(self, g):
        GenericASTTraversal.__init__(self, None)
        self.gv = __import__('gv')
        self.g = g

    def convert(self, ast):
        self.preorder(ast)

    def n_element(self, n):
        gn = n.data['gv']
        if len(n) == 0:
            w, h = (str(p / 72.0) for p in n.style.size)
            self.gv.setv(gn, 'width', w)
            self.gv.setv(gn, 'height', h)
        else:
            w, h = n.style.size
            bottom = n.style.padding.bottom
            # a hack for cluster label and node alignment
            self.gv.setv(gn, 'fontsize', str((h - bottom)))
            self.gv.setv(gn, 'label', 'A')

    def n_dependency(self, n):
        gn = n.data['gv']
        self.gv.setv(gn, 'minlen', str(250.0 / 72))

    n_generalization = n_association = n_dependency


class FromGVConverter(GenericASTTraversal):
    def __init__(self, g):
        GenericASTTraversal.__init__(self, None)
        self.gv = __import__('gv')
        self.g = g
        self.size = Size(0, 0)

    def convert(self, ast):
        self.preorder(ast)


    def _get_pos(self, n):
        gn = n.data['gv']
        gv = self.gv
        w, h = self._get_size(n)
        dw, dh = self.size
        if len(n) == 0:
            x, y = map(float, gv.getv(gn, 'pos').split(','))
            x = x - w / 2.0
            y = dh - y - h / 2.0
        else:
            x, y = map(float, gv.getv(gn, 'bb').split(','))[:2]
            y = dh - y - h
        return Pos(x, y)


    def _get_size(self, n):
        gv = self.gv
        gn = n.data['gv']
        if len(n) == 0:
            return float(gv.getv(gn, 'width')) * 72.0, float(gv.getv(gn, 'height')) * 72.0
        else:
            x, y, w, h = map(float, gv.getv(gn, 'bb').split(','))
            return Size(w - x, h - y)

    def n_diagram(self, n):
        n.style.pos = Pos(0, 0)
        self.size = n.style.size = self._get_size(n)


    def n_element(self, n):
        #print n.name, 'qq', gv.getv(gn, 'pos')
        n.style.pos = self._get_pos(n)
        n.style.size = self._get_size(n)

    def n_dependency(self, n):
        gn = n.data['gv']
        gv = self.gv
        dw, dh = self.size
        p = gv.getv(gn, 'pos').split()
        n.style.edges = tuple(Pos(float(t.split(',')[0]), dh - float(t.split(',')[1])) for t in p)

    n_generalization = n_association = n_dependency



class GVGraph(GenericASTTraversal):
    """
    Generate Graphviz graph structure.

    Graph information is injected into Node.data['gv'].
    """
    def __init__(self):
        GenericASTTraversal.__init__(self, None)
        self.gv = __import__('gv')
        self.g = None

    def create(self, ast):
        self.preorder(ast)

    def layout(self, ast):
        gv = self.gv
        g = self.g

        converter = ToGVConverter(g)
        converter.convert(ast)

        gv.layout(g, 'dot')
        gv.render(g, 'xdot')
        #gv.render(g, 'svg', 'a.svg')

        converter = FromGVConverter(g)
        converter.convert(ast)

    def n_diagram(self, n):
        self.g = g = self.gv.digraph('G')
        self.gv.setv(g, 'compound', 'true')
        self.gv.setv(g, 'clusterrank', 'local')
        #self.gv.setv(g, 'rankdir', 'LR')
        #self.gv.setv(g, 'mindist', '1000')
        self.gv.setv(g, 'nodesep', str(50 / 72.0))
        n.data['gv'] = g


#    def n_diagram_exit(self, node):
#        self._data.append('}')


    def n_element(self, n):
        """
        Generate UML element.
        """
        global filename, lineno
        g = self.g
        gv = self.gv

        if n.parent.type == 'element':
            g = n.parent.data['gv']

        if len(n) == 0:
            id = n.id
            gn = gv.node(g, id)
        else:
            id = 'cluster_' + n.id
            gn = gv.graph(g, id)
        gv.setv(gn, 'id', id)
        gv.setv(gn, 'shape', 'box')
#        if n.name:
#            gv.setv(gn, 'label', n.name)
        n.data['gv'] = gn


    def get_edge(self, node):

        t = node.tail
        if len(node.tail) > 0:
            t = node.tail[0]

        h = node.head
        if len(node.head) > 0:
            h = node.head[0]

        gv = self.gv
        g = self.g

        gt = t.data['gv']
        gh = h.data['gv']
        e = gv.edge(gt, gh)

        gv.setv(e, 'arrowhead', 'none')
        gv.setv(e, 'arrowtail', 'none')

        if len(node.tail) > 0:
            t = node.tail
            gv.setv(e, 'ltail', gv.getv(t.data['gv'], 'id'))

        if len(node.head) > 0:
            h = node.head
            gv.setv(e, 'lhead', gv.getv(h.data['gv'], 'id'))

        return e 


    def n_dependency(self, n):
        e = self.get_edge(n)
        n.data['gv'] = e

    n_generalization = n_association = n_dependency

    def n_comment(self, node):
        """
        Process comment node, which is ignored.
        """
        pass


    def n_empty(self, node):
        """
        Process empty node, which is ignored.
        """
        pass



