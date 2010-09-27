# the idea of piUML

artifact f 'model.pml' <<piuml, source>>
component c 'piUML'
    component cr 'Renderer'
    component cl 'Layout'
    component cp 'Parser'
artifact m 'model.pdf' <<document>>

f <u- cp
cr -> <<create>> m

cp <- cl
cl <- cr

:layout:
    center: cr cl cp

# vim: sw=4:et:ai
