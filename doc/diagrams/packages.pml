package pu 'piuml'
    package pp 'parser'
    package pr 'renderer'
    package pl 'layout'
    package pd 'data'

pp -i> pd
pr -i> pd
pl -i> pd

:layout:
    center: pp pr pl
    middle: pr pd

# vim: sw=4:et:ai
