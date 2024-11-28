from typing import Dict, List, Tuple
import tkinter
import tkinter.font

from Tag import Tag
from Text import Text

class Layout:
    HSTEP, VSTEP = 13, 18

    def __init__(self, tokens: List[Tag | Text], browser_width: int):
        self.display_list: List[Tuple[int, int, str, tkinter.font.Font]] = []
        self.line: List[Tuple[int, str, tkinter.font.Font]] = []
        self.fonts: Dict[Tuple[int, str, str]] = {}
        self.cursor_x, self.cursor_y = self.HSTEP, self.VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12
        self.content_height = 0

        for tok in tokens:
            self.token(tok, browser_width)

        self.flush()

    def token(self, token: Tag | Text, browser_width: int) -> None:
        if isinstance(token, Text):
            for word in token.text.split():
                self.word(word, browser_width)
        elif isinstance(token, Tag):
            if token.tag == "i":
                self.style = "italic"
            elif token.tag == "/i":
                self.style = "roman"
            elif token.tag == "b":
                self.weight = "bold"
            elif token.tag == "/b":
                self.weight = "normal"
            elif token.tag == "small":
                self.size -= 2
            elif token.tag == "/small":
                self.size += 2
            elif token.tag == "big":
                self.size += 4
            elif token.tag == "/big":
                self.size -= 4
            elif token.tag == "br":
                if self.line == []:
                    self.cursor_y += self.VSTEP
                else:
                    self.flush()
            elif token.tag == "/p":
                self.flush()
                self.cursor_y += self.VSTEP

    def word(self, word: str, browser_width: int) -> None:
        font = self.get_font(self.size, self.weight, self.style)
        w = font.measure(word)
        if self.cursor_x + w >= browser_width - self.HSTEP:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
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
