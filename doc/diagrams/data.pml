class n "Node: list"
#    : parent: Node = None
    : type: str
    : element: str
    : id: str = uuid()
    : name: str = ''
    : stereotypes: list = []
    : data: dict = {}
    : is_packaging(): bool

class e "Edge"
    : tail: Node
    : head: Node

class style "Style"
    : pos: Pos
    : size: Size
    : edges: Pos[*]
    : padding: Area
    : margin: Area
    : inner: Area

class a "Area: tuple"
    : top: float
    : right: float
    : bottom: float
    : left: float

class p "Pos: tuple"
    : x: float
    : y: float

class s "Size: tuple"
    : width: float
    : height: float

e => n
#n -> style <<AAAA>>
n =>=> 'has style' style
    : [1]
    : style [1]
#n ==> n # parent
#n ==> n # 0..* children

:layout:
    center: n e

# vim: sw=4:et:ai
