#
# piUML data model
#

class e "Element"
    : cls: str
    : id: str = uuid()
    : stereotypes: list = []
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

e =<= "packages" p
    : children [0..*]
    : parent [0..1]

:layout:
    middle: e p
    center: e r
    center: p d

# vim: sw=4:et:ai
