class d1 <<align>> 'Default'
    class dc1 'A'
    class dc2 'B'
        class dc3 'C'
        class dc4 'D'

class t1 <<align>> 'Top'
    class tc1 'A'
    class tc2 'B'
        class tc3 'C'
        class tc4 'D'

class b1 <<align>> 'Bottom'
    class bc1 'A'
    class bc2 'B'
        class bc3 'C'
            : c1()
            : c2()
            : c3()
        class bc4 'D'

:layout:
    bottom: bc1 bc3

class r1 <<align>> 'Right'
    class rc1 'A'
#    :<<align>>:
#        : right = A C
    class rc2 'B'
        class rc3 'Copy Reference'
        class rc4 'D'

:layout:
    right: rc1 rc3
    center: d1 t1 b1
