# the idea of piUML

artifact f 'model.txt' <<piuml, source>>
component c 'piUML'
    component cp 'Parser'
    component cl 'Layout'
    component cr 'Renderer'
artifact m 'model.pdf' <<document>>

f <u- cp
cr -> <<create>> m

cp <- cl
cl <- cr

align=center: cp f
align=center: cr m

# vim: sw=4:et:ai