#
# piUML data model
#

class n "Node: list"
#    : parent: Node = None
    : type: str
    : element: str
    : id: str = uuid()
    : name: str = ''
    : stereotypes: list = []
    : data: dict = {}
    : is_packaging(): bool

class e "Element"

class l "Line"
    : tail: Node [1]
    : head: Node [1]

class i "IElement"

class s "Style"

e => n
l => n
i => n

n =>=> 'has style' s
    : [1]
    : style [1]

#n =>=> n
#    : parent [1]
#    : items [0..*]

:layout:
    top: e l i
    center: l n
    middle: n s

# vim: sw=4:et:ai
