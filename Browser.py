import platform
import tkinter as tk
from typing import List

from HTMLParser import HTMLParser
from HTTPConnection import HTTPConnection
from HTTPRequestCache import HTTPRequestCache
from Layout import Layout
from Text import Text
from URL import URL

class Browser:
    INITIAL_WIDTH, INITIAL_HEIGHT = 800, 600
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

    def move_scroll(self, delta: int) -> None:
        self.scroll += delta
        if self.scroll < 0: self.scroll = 0
        elif self.scroll + self.height > self.layout.content_height: self.scroll = max(self.layout.content_height - self.height, 0)

    def load(self, url: URL) -> None:
        conn = HTTPConnection(url, HTTPRequestCache())
        body = conn.request()
        if not url.view_source:
            self.nodes = HTMLParser(body).parse()
            self.layout = Layout(self.nodes, self.width)
        else:
            self.layout = Layout(Text(body, None), self.width)
        self.draw()

    def draw_scrollbar(self) -> None:
        if self.layout.content_height == 0:
            return

        viewport_height = self.layout.content_height
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

        self.canvas.create_rectangle(self.width - Layout.HSTEP, scrollbar_start_height, self.width, scrollbar_end_height, fill="blue", tags="scrollbar")

    def draw(self) -> None:
        self.canvas.delete("all")
        for x, y, c, font in self.layout.display_list:
            if y > self.scroll + self.height: continue
            if y + Layout.VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw", font=font)
        self.draw_scrollbar()

    def scrolldown(self, e: tk.Event) -> None:
        self.move_scroll(self.SCROLL_STEP)
        self.draw()

    def scrollup(self, e: tk.Event) -> None:
        self.move_scroll(-self.SCROLL_STEP)
        self.draw()

    def mousescroll(self, e: tk.Event) -> None:
        if self.platform == "Windows":
            self.move_scroll(-((e.delta // 120) * Layout.VSTEP))
        elif self.platform == "Darwin":
            self.move_scroll(e.delta * Layout.VSTEP)
        self.draw()

    def resize(self, e: tk.Event) -> None:
        self.width = e.width
        self.height = e.height
        self.layout = Layout(self.nodes, self.width)
        self.draw()
