from Element import Element

class Text:
    def __init__(self, text: str, parent: Element):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self) -> str:
        return repr(self.text)
