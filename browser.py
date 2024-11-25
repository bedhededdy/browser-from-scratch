import socket
import ssl
import tkinter

# TODO: EXERCISE 1-7

class URL:
    def __init__(self, url: str):
        self.view_source = False
        self.socket = None
        self.socket_stream = None
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

    def request(self) -> str:
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

            request = "GET {} HTTP/1.1\r\n".format(self.path)
            request += "Host: {}\r\n".format(self.host)
            request += "Connection: Keep-Alive\r\n" # By default, try to keep the connection alive
            request += "User-Agent: PyBrowse-1.0\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = self.socket_stream
            statusline = response.readline().decode("utf8")
            version, status, explanation = statusline.split(" ", 2)
            response_headers = {}
            while True:
                line = response.readline().decode("utf8")
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers
            if response_headers["connection"] == "close":
                # FIXME: WE ARE ASSUMING HERE THAT THE ENTIRE MESSAGE BODY
                #        IS PRESENT AT THIS POINT IN THE STREAM INTEAD OF
                #        READING CONTENT-LENGTH BYTES
                content = response.read().decode("utf8")
                self.socket_stream.close()
                s.close()
                self.socket = None
                self.socket_stream = None
            else:
                content_length = int(response_headers["content-length"])
                content = response.read(content_length).decode("utf8")
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

    def close(self) -> None:
        if self.socket != None:
            self.socket_stream.close()
            self.socket.close()
            self.socket = None
            self.socket_stream = None

def show(body: str, view_source: bool):
    if view_source:
        print(body, end="")
        return
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
                    print(c + entity + " ", end="")
                elif body[i] == "<":
                    print(c + entity, end="")
                    # Have to do this so that we hit the tag open in next
                    # loop iteration
                    i -= 1
                elif body[i] == ";":
                    # Potentially an entity
                    if entity == "lt":
                        print("<", end="")
                    elif entity == "gt":
                        print(">", end="")
                    else:
                        # Not a valid entity, so just print the raw text
                        print(c + entity + ";", end="")
            else:
                print(c, end="")
        i += 1

def load(url: URL):
    body = url.request()
    show(body, url.view_source)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        url = "file://example.html"
    else:
        url = sys.argv[1]
    url_obj = URL(url)
    load(url_obj)
