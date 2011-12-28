# default piUML instance specification

instance p ':Parser'
instance l ':Layout'
instance r ':Renderer'
instance ast ':Diagram'

p -> <<create>> ast
l -> <<process>> ast
r -u> ast

:layout:
    top: p l r
    center: l ast

# vim: sw=4:et:ai
