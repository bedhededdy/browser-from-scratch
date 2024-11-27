import platform
import tkinter as tk
from time import time
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
        self.content_height = 0

        self.platform = platform.system()
        if self.platform == "Linux":
            self.window.bind("<Button-4>", self.scrollup)
            self.window.bind("<Button-5>", self.scrolldown)
        else:
            self.window.bind("<MouseWheel>", self.mousescroll)
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

        self.window.bind("<Configure>", self.resize)

        self.canvas.tag_bind("scrollbar", "<Button-1>", self.start_scroll)
        self.canvas.tag_bind("scrollbar", "<B1-Motion>", self.do_scroll)
        self.canvas.tag_bind("scrollbar", "<ButtonRelease-1>", self.end_scroll)

    def move_scroll(self, delta: int) -> None:
        self.scroll += delta
        if self.scroll < 0: self.scroll = 0
        elif self.scroll + self.height > self.content_height: self.scroll = self.content_height - self.height

    def start_scroll(self, e: tk.Event) -> None:
        self.start_scroll_y = e.y
        self.calls_since_last_draw = 0

    def do_scroll(self, e: tk.Event) -> None:
        delta = e.y  - self.start_scroll_y
        self.move_scroll(delta)
        self.calls_since_last_draw += 1
        if self.calls_since_last_draw == 20:
            # FIXME: CALLING DRAW UNBINDS THIS FROM THE ORIGINAL OBJECT
            #        AND SO WE NEVER GET CALLED AGAIN
            #        EVEN IF WE REBIND THE TAGS IN THE DRAW CALL
            #        WE WOULD NEED TO START PERSISTING OBJECTS BETWEEN FRAMES
            #        TO FIX THIS INSTEAD OF DELETING ALL IN THE DRAW CALL
            self.draw()
            self.calls_since_last_draw = 0

    def end_scroll(self, e: tk.Event) -> None:
        self.start_scroll_y = None
        self.calls_since_last_draw = 0

    def load(self, url: URL) -> None:
        conn = HTTPConnection(url, HTTPRequestCache())
        body = conn.request()
        self.text = lex(body, url.view_source)
        self.display_list = self.layout()
        self.draw()

    def draw_scrollbar(self) -> None:
        if self.content_height == 0:
            return

        viewport_height = self.content_height
        visible_viewport_height = self.height
        visible_viewport_percentage = visible_viewport_height / viewport_height
        viewport_start_percentage = self.scroll / viewport_height
        viewport_end_percentage = viewport_start_percentage + visible_viewport_percentage
        if viewport_end_percentage > 1.0:
            viewport_start_percentage = viewport_end_percentage - visible_viewport_percentage
            viewport_end_percentage = 1.0

        scrollbar_start_height = viewport_start_percentage * self.height
        scrollbar_end_height = viewport_end_percentage * self.height

        # FIXME: HANDLE FLOATING POINT FUCKERY
        if visible_viewport_percentage >= 1.0:
            return

        self.canvas.create_rectangle(self.width - self.HSTEP, scrollbar_start_height, self.width, scrollbar_end_height, fill="blue", tags="scrollbar")
        self.canvas.tag_bind("scrollbar", "<Button-1>", self.start_scroll)
        self.canvas.tag_bind("scrollbar", "<B1-Motion>", self.do_scroll)
        self.canvas.tag_bind("scrollbar", "<ButtonRelease-1>", self.end_scroll)

    def draw(self) -> None:
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: continue
            if y + self.VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
        self.draw_scrollbar()

    def scrolldown(self, e: tk.Event) -> None:
        self.move_scroll(self.SCROLL_STEP)
        self.draw()

    def scrollup(self, e: tk.Event) -> None:
        self.move_scroll(-self.SCROLL_STEP)
        self.draw()

    def mousescroll(self, e: tk.Event) -> None:
        if self.platform == "Windows":
            self.move_scroll(-((e.delta // 120) * self.VSTEP))
        elif self.platform == "Darwin":
            self.move_scroll(e.delta * self.VSTEP)
        self.draw()

    def resize(self, e: tk.Event) -> None:
        self.width = e.width
        self.height = e.height
        self.display_list = self.layout()
        self.draw()

    def layout(self) -> List[Tuple[int, int, str]]:
        display_list = []
        self.content_height = 0
        cursor_x, cursor_y = Browser.HSTEP, Browser.VSTEP
        for c in self.text:
            if c == "\n":
                cursor_x = Browser.HSTEP
                cursor_y += Browser.VSTEP
                self.content_height = max(cursor_y, self.content_height)
                continue
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += Browser.HSTEP
            if cursor_x >= self.width - Browser.HSTEP:
                cursor_x = Browser.HSTEP
                cursor_y += Browser.VSTEP
            self.content_height = max(cursor_y, self.content_height)
        return display_list
