from typing import List

from Element import Element
from Text import Text

class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"
    ]

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script"
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished: List[Element] = []
        # TODO: THIS SHOULDN'T BE A CLASS MEMBER
        self.in_script = False

    def parse(self) -> Element:
        text = ""
        in_tag = False
        for i, c in enumerate(self.body):
            if c == "<":
                if (self.in_script and self.body[i+1:i+8] != "/script") or (in_tag and text.startswith("!--")):
                    text += c
                    continue
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                if not self.add_tag(text):
                    in_tag = False
                    text = ""
                else:
                    text += c
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text: str) -> None:
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        # TODO: HAVE TO ADD THE ENTITY DETECTION BACK IN
        #       (DO IT AFTER GETTING THE WHOLE ASS BUFFER)
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag: str) -> bool:
        if tag.startswith("!"):
            if len(tag) == 3 and tag == "!--":
                return True
            elif tag.startswith("!--"):
                if len(tag) == 4 and tag.endswith("--"):
                    return True
                elif tag.endswith("--"):
                    return False
                else:
                    return True
            else:
                return False
        tag, attributes = self.get_attributes(tag)
        self.implicit_tags(tag)
        ret_val = self.in_script
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            self.unfinished.pop()
            if tag == "/script":
                self.in_script = False
                ret_val = False
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            if parent and ((tag == "p" and parent.tag == "p") or (tag == "li" and parent.tag == "li")):
                parent = parent.parent
            node = Element(tag, attributes, parent)
            if parent: parent.children.append(node)
            self.unfinished.append(node)
            if tag == "script": self.in_script = True
        return ret_val

    def get_attributes(self, text: str):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes

    def implicit_tags(self, tag: str | None) -> None:
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self) -> Element:
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            self.unfinished.pop()
        res = self.unfinished.pop()
        # print_tree(res)
        return res

def print_tree(node: Text | Element, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
