class r <<device>> 'Reader'

class p 'Publication'
    : title: str
    : authors: list

class b 'Book'
    : isbn: str

r O==> p
    : [0..1]
    : publications [1..*]

p <= b

:layout:
    center: p b

# vim: sw=4:et:ai
