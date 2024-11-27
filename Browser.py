import platform
import tkinter as tk
from typing import List, Tuple

from HTTPConnection import HTTPConnection
from HTTPRequestCache import HTTPRequestCache
from URL import URL

def lex(body: str, view_source: bool) -> str:
    if view_source:
        return body
    text = ""
    in_tag = False
    i = 0
    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            if c == "&":
                entity = ""
                i = i + 1
                while i < len(body) and body[i] != " " and body[i] not in [";", "<"]:
                    entity += body[i]
                    i += 1
                if i == len(body):
                    # Should never happen in valid HTML
                    break
                elif body[i] == " ":
                    # Wasn't an entity
                    text += c + entity + " "
                elif body[i] == "<":
                    text += c + entity
                    # Have to do this so that we hit the tag open in next
                    # loop iteration
                    i -= 1
                elif body[i] == ";":
                    # Potentially an entity
                    if entity == "lt":
                        text += "<"
                    elif entity == "gt":
                        text += ">"
                    else:
                        # Not a valid entity, so just print the raw text
                        text += c + entity + ";"
            else:
                text += c
        i += 1
    return text

class Browser:
    INITIAL_WIDTH, INITIAL_HEIGHT = 800, 600
    HSTEP, VSTEP = 13, 18
    SCROLL_STEP = 100

    def __init__(self):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=self.INITIAL_WIDTH, height=self.INITIAL_HEIGHT)
        self.canvas.pack(fill="both", expand=True)
        self.width = self.INITIAL_WIDTH
        self.height = self.INITIAL_HEIGHT
        self.scroll = 0

        self.platform = platform.system()
        if self.platform == "Linux":
            self.window.bind("<Button-4>", self.scrollup)
            self.window.bind("<Button-5>", self.scrolldown)
        else:
            self.window.bind("<MouseWheel>", self.mousescroll)
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

        self.window.bind("<Configure>", self.resize)

    def load(self, url: URL) -> None:
        conn = HTTPConnection(url, HTTPRequestCache())
        body = conn.request()
        self.text = lex(body, url.view_source)
        self.display_list = self.layout()
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: continue
            if y + self.VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e: tk.Event) -> None:
        self.scroll += self.SCROLL_STEP
        self.draw()

    def scrollup(self, e: tk.Event) -> None:
        self.scroll -= self.SCROLL_STEP
        if self.scroll < 0: self.scroll = 0
        self.draw()

    def mousescroll(self, e: tk.Event) -> None:
        if self.platform == "Windows":
            self.scroll -= (e.delta // 120) * self.VSTEP
        elif self.platform == "Darwin":
            self.scroll += e.delta * self.VSTEP
        if self.scroll < 0: self.scroll = 0
        self.draw()

    def resize(self, e: tk.Event) -> None:
        self.width = e.width
        self.height = e.height
        self.display_list = self.layout()
        self.draw()

    def layout(self) -> List[Tuple[int, int, str]]:
        display_list = []
        cursor_x, cursor_y = Browser.HSTEP, Browser.VSTEP
        for c in self.text:
            if c == "\n":
                cursor_x = Browser.HSTEP
                cursor_y += Browser.VSTEP
                continue
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += Browser.HSTEP
            if cursor_x >= self.width - Browser.HSTEP:
                cursor_x = Browser.HSTEP
                cursor_y += Browser.VSTEP
        return display_list
