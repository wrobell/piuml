# piUML use cases

actor w 'Writer'

subsystem pu 'piUML'
    usecase m 'Create Model'

subsystem doc 'Documentation'
    usecase wd 'Create'

comment c 'For example\n\n- Sphinx\n- Epydoc\n- TeX\n'

#w ==> m
#w ==> wd

m -e> wd
doc -- c

align=center: pu doc
align=middle: doc c
align=middle: w pu

# vim: sw=4:et:ai