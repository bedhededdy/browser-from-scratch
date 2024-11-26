from typing import Dict

from URL import URL

class HTTPRequestCache:
    def __init__(self):
        self.cache: Dict[URL, str] = {}

    def get_cached_request(self, url: URL) -> str | None:
        if url in self.cache:
            return self.cache[url]
        return None

    def set_cached_request(self, url: URL, content: str) -> None:
        self.cache[url] = content

    def clear_cached_request(self, url: URL) -> None:
        if url in self.cache:
            del self.cache[url]

    def clear(self) -> None:
        self.cache.clear()
