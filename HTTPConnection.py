import gzip
from io import BufferedReader
import ssl
import socket
from typing import Dict

from HTTPRequestCache import HTTPRequestCache
from URL import URL

class HTTPConnection:
    MAX_REDIRECTS = 10

    def __init__(self, url: URL, cache: HTTPRequestCache | None = None):
        self.url = url
        self.socket: socket.socket | ssl.SSLSocket | None = None
        self.socket_stream: BufferedReader | None  = None
        self.cache = cache

    def request(self) -> str:
        if self.url.scheme in ["http", "https"]:
            return self.__http_request(self.url)
        elif self.url.scheme == "data":
            return self.__data_request()
        elif self.url.scheme == "file":
            return self.__file_request()
        return ""

    def __http_request(self, base_url: URL, nredirects = 0) -> str:
        # TODO: NOT RESPECTING HTTP REQUEST CACHING POLICY

        if self.socket == None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            s.connect((self.url.host, self.url.port))
            if self.url.secure():
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.url.host)
            self.socket = s
            self.socket_stream = s.makefile("rb", newline="\r\n")

        if self.cache:
            cached_response = self.cache.get_cached_request(self.url)
            # TODO: I THINK WE NEED TO EXPLICITLY CHECK FOR NULL VS EMPTY STRING
            if cached_response:
                return cached_response

        request =  "GET {} HTTP/1.1\r\n".format(self.url.path)
        request += "Host: {}\r\n".format(self.url.host)
        request += "Connection: Keep-Alive\r\n"
        request += "User-Agent: PyBrowse-1.0\r\n"
        request += "Accept-Encoding: gzip\r\n"
        request += "\r\n"
        self.socket.send(request.encode("utf8"))

        response = self.socket_stream

        status_line = response.readline().decode("utf8")
        version, status, explanation = status_line.split(" ", 2)
        status = int(status)

        response_headers: Dict[str, str] = {}
        while True:
            line = response.readline().decode("utf8")
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert version == "HTTP/1.1"
        if status >= 300 and status < 400:
            assert status != 300 and status != 306
            assert status < 309
            if status != 304:
                new_url_str: str = response_headers["location"]
                if nredirects == self.MAX_REDIRECTS:
                    self.close()
                    # TODO: HANDLE PROPERLY
                    return "ERROR: TOO MANY REDIRECTS"
                if new_url_str.startswith("/"):
                    self.set_path(new_url_str)
                    self.__read_http_content(response_headers)
                else:
                    new_url_obj = URL(new_url_str)
                    if new_url_obj.scheme != self.url.scheme or new_url_obj.host != self.url.host or new_url_obj.port != self.url.port:
                        self.close()
                        assert new_url_obj.scheme in ["http", "https"]
                        self.url = new_url_obj
                    else:
                        self.__read_http_content(response_headers)
                        self.set_path(new_url_obj.path)
                return self.__http_request(base_url, nredirects + 1)

        content = self.__read_http_content(response_headers)

        if "connection" in response_headers and response_headers["connection"].casefold() == "close":
            self.close()

        if self.cache and (status == 200 or status == 404 or status == 301):
            # TODO: CAN ONLY CACHE GET REQUESTS
            # TODO: CAN POTENTIALLY CACHE MORE REQUESTS
            if "cache-control" in response_headers:
                cache_control = response_headers["cache-control"].casefold()
                if cache_control.startswith("max-age"):
                    self.cache.set_cached_request(self.url, content, int(cache_control.split("=", 1)[1]))

        return content

    def __read_http_content(self, response_headers: Dict[str, str]) -> str:
        if "transfer-encoding" in response_headers:
            assert response_headers["transfer-encoding"].casefold() == "chunked"
            return self.__read_http_chunks(response_headers.get("content-encoding", None))
        else:
            assert "content-length" in response_headers
            raw_content = self.socket_stream.read(int(response_headers["content-length"]))
            if "content-encoding" in response_headers:
                assert response_headers["content-encoding"].casefold() == "gzip"
                gzip.decompress(raw_content)
            return raw_content.decode("utf8")

    def __read_http_chunks(self, content_encoding: str | None = None) -> str:
        content = bytes()
        while True:
            content_length = self.socket_stream.readline().decode("utf8").strip()
            if content_length != "": content_length = int(content_length, 16)
            else: content_length = 0
            if content_length == 0:
                self.socket_stream.readline()
                break
            content += self.socket_stream.read(content_length)
        if content_encoding == "gzip":
            content = gzip.decompress(content)
        return content.decode("utf8")

    def __data_request(self) -> str:
        return self.url.data

    def __file_request(self) -> str:
        # TODO: ERRORS
        with open(self.url.path, mode="r", encoding="utf8") as f:
            return f.read()

    def set_path(self, path: str) -> None:
        self.url.path = path

    def is_secure(self) -> bool:
        return self.url.secure()

    def close(self) -> None:
        if self.socket == None:
            return
        self.socket_stream.close()
        self.socket.close()
        self.socket_stream = None
        self.socket = None
