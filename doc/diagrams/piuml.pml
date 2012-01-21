# the idea of piUML

component c 'piUML'
    component cp 'Parser'
    component cl 'Layout'
    component cr 'Renderer'

component fs <<actor>> 'Filesystem'
    artifact f <<piuml, source>> 'model.pml'
    artifact m <<document>> 'model.pdf'

f <u- cp
cr -> <<create>> m

cp <- cl
cl <- cr

:layout:
    center: cp f
    center: cr m

# vim: sw=4:et:ai
