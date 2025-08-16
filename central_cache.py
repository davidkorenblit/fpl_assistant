import time
import hashlib
from typing import Any, Optional

class CentralCache:
    def __init__(self, timeout: int = 1800):
        self.cache = {}
        self.timeout = timeout

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            timestamp, data = self.cache[key]
            if time.time() - timestamp < self.timeout:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = (time.time(), value)

    def clear(self):
        self.cache.clear()

    def make_key(self, *args, **kwargs) -> str:
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()

cache = CentralCache()