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

align=top: p l r
align=center: l ast

# vim: sw=4:et:ai
