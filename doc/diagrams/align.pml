class d1 'Default' <<align>>
    class dc1 'A'
    class dc2 'B'
        class dc3 'C'
        class dc4 'D'

class t1 'Top' <<align>>
    class tc1 'A'
    class tc2 'B'
        class tc3 'C'
        class tc4 'D'

class b1 'Bottom' <<align>>
    class bc1 'A'
    class bc2 'B'
        class bc3 'C'
            : c1()
            : c2()
            : c3()
        class bc4 'D'

align=bottom: bc1 bc3

class r1 'Right' <<align>>
    class rc1 'A'
#    :<<align>>:
#        : right = A C
    class rc2 'B'
        class rc3 'Copy Reference'
        class rc4 'D'

align=right: rc1 rc3

align=center: d1 t1 b1
