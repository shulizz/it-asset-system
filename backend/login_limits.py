"""Bounded, thread-safe login throttling for the single-process deployment."""

from collections import OrderedDict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException


class LoginLimiter:
    def __init__(self, message="登录尝试过于频繁，请稍后重试"):
        self._attempts = OrderedDict()
        self._lock = Lock()
        self.message = message

    def clear(self):
        with self._lock:
            self._attempts.clear()

    def check(self, address, username):
        now = monotonic()
        keys = [(("address", address), 30), (("account", username), 10)]
        with self._lock:
            for key, limit in keys:
                attempts = self._attempts.setdefault(key, deque())
                self._attempts.move_to_end(key)
                while attempts and attempts[0] <= now - 60:
                    attempts.popleft()
                if len(attempts) >= limit:
                    raise HTTPException(429, self.message, headers={"Retry-After": "60"})
            for key, _ in keys:
                self._attempts[key].append(now)
            while len(self._attempts) > 4096:
                self._attempts.popitem(last=False)


login_limiter = LoginLimiter()
password_limiter = LoginLimiter("密码验证过于频繁，请一分钟后重试")
