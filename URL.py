class URL:
    def __init__(self, url: str):
        self.view_source = False
        self.scheme = ""

        # Only present in data URLs
        self.dtype = ""
        self.data = ""

        # Only present in HTTP and HTTPS URLs
        self.host = ""
        self.port = -1
        self.path = ""

        if "://" in url:
            self.scheme, url = url.split("://", 1)
            if self.scheme.startswith("view-source:"):
                self.view_source = True
                self.scheme = self.scheme[12:]
        else:
            # TODO: DOES VIEW-SOURCE WORK ON DATA URLS?
            #       ANSWER: YES, AND WE DON'T HANDLE IT
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

    def secure(self) -> bool:
        return self.scheme == "https"

    def __str__(self) -> str:
        url_str = "{}://{}:{}{}".format(self.scheme, self.host, self.port, self.path)
        if self.view_source:
            url_str = "view-source:" + url_str
        return url_str

    def __hash__(self) -> int:
        # TODO: CAN WE CACHE HTTP/HTTPS INTERCHANGEABLY?
        #       I WOULD ARGUE YES, BUT FOR NOW LET'S NOT
        return hash((self.scheme, self.host, self.port, self.path))
