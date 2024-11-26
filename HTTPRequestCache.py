from time import time
from typing import Dict

from URL import URL

class HTTPRequestCache:
    def __init__(self):
        self.cache: Dict[URL, str] = {}

    def get_cached_request(self, url: URL) -> str | None:
        if url in self.cache:
            cache_unix_time, expiry, content = self.cache[url]
            if int(time()) - cache_unix_time >= expiry:
                self.clear_cached_request(url)
                return None
            return content
        return None

    def set_cached_request(self, url: URL, content: str, expiry: int) -> None:
        self.cache[url] = (int(time()), expiry, content)

    def clear_cached_request(self, url: URL) -> None:
        if url in self.cache:
            del self.cache[url]

    def clear(self) -> None:
        self.cache.clear()
