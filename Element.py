from typing import List

class Element:
    # Can't type the parent parameter as Element because Python
    # doesn't recognize it as a type until inside the body of __init__
    def __init__(self, tag: str, attributes, parent):
        self.tag = tag
        self.parent: Element = parent
        self.children: List[Element] = []
        self.attributes = attributes

    def __repr__(self) -> str:
        return "<" + self.tag + ">"
