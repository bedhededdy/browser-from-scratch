from typing import Dict, List, Tuple
import tkinter
import tkinter.font

from Element import Element
from Text import Text

class Layout:
    HSTEP, VSTEP = 13, 18

    def __init__(self, nodes: List[Element | Text], browser_width: int):
        self.display_list: List[Tuple[int, int, str, tkinter.font.Font]] = []
        self.line: List[Tuple[int, str, tkinter.font.Font]] = []
        self.fonts: Dict[Tuple[int, str, str]] = {}
        self.cursor_x, self.cursor_y = self.HSTEP, self.VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.content_height = 0

        # FIXME: WE CALL IT NODES, BUT ATM IT'S A SINGLE ELEMENT
        self.recurse(nodes, browser_width)

        self.flush()

    def open_tag(self, tag: str) -> None:
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            if self.line == []:
                self.cursor_y += self.VSTEP
            else:
                self.flush()

    def close_tag(self, tag: str) -> None:
        if tag == "/i":
            self.style = "roman"
        elif tag == "/b":
            self.weight = "normal"
        elif tag == "/small":
            self.size += 2
        elif tag == "/big":
            self.size -= 4
        elif tag == "/p":
            self.flush()
            self.cursor_y += self.VSTEP

    def recurse(self, tree: Text | Element, browser_width: int) -> None:
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word, browser_width)
        elif isinstance(tree, Element):
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child, browser_width)
            self.close_tag(tree.tag)

    def word(self, word: str, browser_width: int) -> None:
        font = self.get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w >= browser_width - self.HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        # FIXME: THIS IS NOT PROPERLY ACCOUNTING FOR THE LINE HEIGHTS
        self.content_height = max(self.cursor_y, self.content_height)

    def flush(self) -> None:
        if not self.line: return
        metrics = [font.metrics() for _, _, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        max_descent = max(metric["descent"] for metric in metrics)
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = self.HSTEP
        self.line = []

    def get_font(self, size: int, weight: str, style: str) -> tkinter.font.Font:
        key = (size, weight, style)
        if key not in self.fonts:
            font = tkinter.font.Font(size=size, weight=weight, slant=style)
            label = tkinter.Label(font=font)
            self.fonts[key] = (font, label)
        return self.fonts[key][0]
