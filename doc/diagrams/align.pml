class d1 'Default'
    class dc1 'A'
    class dc2 'B'
        class dc3 'C'
        class dc4 'D'

class t1 'Top'
    class tc1 'Base'
    class tc2 'B'
        class tc3 <<horizontalspan>> 'AlignedWithBase'
        class tc4 'D'

:layout:
    top: tc1 tc3

class b1 'Bottom'
    class bc1 'Base'
    class bc2 'B'
        class bc3 <<horizontalspan>> 'AlignedWithBase'
        class bc4 'D'

:layout:
    bottom: bc1 bc3

class l1 'Left'
    class lc1 <<node>> 'Base'
    class lc2 'B'
        class lc4 <<verticalspan>> 'AlignedWithBase'
        class lc3 'C'

:layout:
    left: lc1 lc4

class r1 'Right'
    class rc1 <<node>> 'Base'
    class rc2 'B'
        class rc3 'C'
        class rc4 <<verticalspan>> 'AlignedWithBase'

:layout:
    right: rc1 rc4

:layout:
    middle: l1 d1 r1
    center: d1 t1 b1
#    center: t1 d1 b1

