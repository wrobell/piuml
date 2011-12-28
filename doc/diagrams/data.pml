#
# piUML data model
#

class s "Stereotype"
    : name: str
    : is_keyword: bool

class e "Element"
    : cls: str
    : id: str = uuid()
    : name: str = ''
    : data: dict = {}

class p "PackagingElement"

class d "Diagram"

class r "Relationship"
    : tail: Element
    : head: Element

#class i "IElement"
#class s "Style"

p => e
d => p
r => e

s <=<= "has" e
    : stereotypes [0..*]

e =<= "packages" p
    : children [0..*]
    : parent [0..1]

:layout:
    middle: e p
    center: e r
    center: p d

# vim: sw=4:et:ai
