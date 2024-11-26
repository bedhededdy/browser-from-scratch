import socket
import ssl
import tkinter as tk
import platform

# TODO: EXERCISE 1-8
# TODO: EXERCISE 2-3

class URL:
    def __init__(self, url: str):
        self.view_source = False
        self.socket = None
        self.socket_stream = None
        self.request_cache = {}
        if "://" in url:
            self.scheme, url = url.split("://", 1)
            if self.scheme.startswith("view-source:"):
                self.view_source = True
                self.scheme = self.scheme[12:]
        else:
            assert url.startswith("data:")
            self.scheme = "data"
            self.dtype, self.data = url[5:].split(",", 1)
            assert self.dtype == "text/html"
        assert self.scheme in ["http", "https", "file", "data"]
        self.port: int | None = None
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        if self.scheme in ["http", "https"]:
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
            self.path = "/" + url
        elif self.scheme == "file":
            self.path = url

    def request(self, nredirects = 0) -> str:
        if self.scheme in ["http", "https"]:
            if self.socket != None:
                s = self.socket
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
                s.connect((self.host, self.port))
                if self.scheme == "https":
                    ctx = ssl.create_default_context()
                    s = ctx.wrap_socket(s, server_hostname=self.host)
                self.socket = s
                self.socket_stream = s.makefile("rb", newline="\r\n")

            cached_response = self.get_cached_response()
            if cached_response:
                # TODO: IT'S NOT THIS SIMPLE, NEED TO RESPECT
                #       CACHE-CONTROL HEADER
                return cached_response[2]

            request = "GET {} HTTP/1.1\r\n".format(self.path)
            request += "Host: {}\r\n".format(self.host)
            request += "Connection: Keep-Alive\r\n" # By default, try to keep the connection alive
            request += "User-Agent: PyBrowse-1.0\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = self.socket_stream

            statusline = response.readline().decode("utf8")
            version, status, explanation = statusline.split(" ", 2)
            status = int(status)

            response_headers = {}
            while True:
                line = response.readline().decode("utf8")
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            # TODO: REMOVE ME ONCE WE ACCEPT THIS
            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            assert version == "HTTP/1.1"
            if status >= 300 and status < 400:
                assert status != 300 and status != 306
                assert status < 309
                if status != 304:
                    new_url: str = response_headers["location"]
                    if nredirects == 10:
                        # Do not exceed 10 redirects
                        self.close()
                        return "ERROR: TOO MANY REDIRECTS"
                    if new_url.startswith("/"):
                        self.set_path(new_url)
                        # FIXME: ASSUMING CONTENT-LENGTH IS SENT
                        response.read(int(response_headers["content-length"]))
                    else:
                        new_url_obj = URL(new_url)
                        if new_url_obj.scheme != self.scheme or new_url_obj.host != self.host or new_url_obj.port != self.port:
                            self.close()
                            # FIXME: NOT GOOD, SERVER COULD TELL US TO OPEN LOCAL FILE AND CRASH
                            self.scheme = new_url_obj.scheme
                            self.host = new_url_obj.host
                            self.port = new_url_obj.port
                        else:
                            # FIXME: ASSUMING CONTENT-LENGTH IS SENT
                            response.read(int(response_headers["content-length"]))
                        self.set_path(new_url_obj.path)
                    return self.request(nredirects + 1)

            # FIXME: ASSUMING CONTENT-LENGTH IS SENT
            content_length = int(response_headers["content-length"])
            content = response.read(content_length).decode("utf8")
            if response_headers["connection"] == "close":
                self.close()

            if status == 200 or status == 404:
                # TODO: CAN ONLY CACHE GET REQUESTS
                # TODO: WE CAN ALSO CACHE OTHER CODES LIKE 301
                #       BUT THAT IS HARDER BECAUSE
                #       THEN WE HAVE TO CACHE THE RESOLVED RESPONSE
                #       INSTEAD OF THE ORIGINAL REDIRECT RESPONSE
                self.request_cache[(self.scheme, self.host, self.port, self.path)] = (statusline, response_headers, content)

            return content
        elif self.scheme == "file":
            # TODO: ERRORS
            with open(self.path, mode="r", encoding="utf8") as f:
                return f.read()
        elif self.scheme == "data":
            return self.data

    def set_path(self, path: str) -> None:
        # Sockets merely connect to a given domain, so changing the path
        # for a given URL object will allow us to send multiple requests
        # to different paths on the same domain over the same socket
        self.path = path

    def get_cached_response(self) -> tuple | None:
        cached = None
        try:
            cached = self.request_cache[(self.scheme, self.host, self.port, self.path)]
        except:
            pass
        return cached

    def close(self) -> None:
        if self.socket != None:
            self.socket_stream.close()
            self.socket.close()
            self.socket = None
            self.socket_stream = None

def lex(body: str, view_source: bool):
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

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

def layout(text, view_source):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in lex(text, view_source):
        if c == "\n":
            cursor_x = HSTEP
            cursor_y += VSTEP
            continue
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_x = HSTEP
            cursor_y += VSTEP
    return display_list

class Browser:
    def __init__(self):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

        self.platform = platform.system()
        if self.platform == "Linux":
            self.window.bind("<Button-4>", self.scrollup)
            self.window.bind("<Button-5>", self.scrolldown)
        else:
            self.window.bind("<MouseWheel>", self.mousescroll)

    def load(self, url: URL):
        body = url.request()
        text = lex(body, url.view_source)
        self.display_list = layout(text, url.view_source)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        if self.scroll < 0: self.scroll = 0
        self.draw()

    def mousescroll(self, e):
        if self.platform == "Windows":
            self.scroll += (e.delta // 120) * VSTEP
        elif self.platform == "Darwin":
            self.scroll += e.delta * VSTEP

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        url = "file://example.html"
    else:
        url = sys.argv[1]
    url_obj = URL(url)
    Browser().load(url_obj)
    tk.mainloop()
