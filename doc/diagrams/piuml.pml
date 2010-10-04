# the idea of piUML

artifact f <<piuml, source>> 'model.pml'
component c 'piUML'
    component cr 'Renderer'
    component cl 'Layout'
    component cp 'Parser'
artifact m <<document>> 'model.pdf'

f <u- cp
cr -> <<create>> m

cp <- cl
cl <- cr

:layout:
    center: cr cl cp

# vim: sw=4:et:ai
