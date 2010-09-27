# default piUML instance specification

instance p ':Parser'
instance l ':MLayout'
instance r ':MRenderer'
instance ast 'ast :Node'
    : type = 'diagram'
    : element = 'diagram'

p -> <<create>> ast
l -> <<process>> ast
r -u> ast

:layout:
    top: p l r
    center: l ast

# vim: sw=4:et:ai
