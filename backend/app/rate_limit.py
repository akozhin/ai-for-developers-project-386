"""Лимит запросов с одного IP в скользящем окне (в памяти процесса)."""

import time
from collections import defaultdict, deque
from http import HTTPStatus

from fastapi import Request

from app.errors import ApiError

AI_REQUESTS_PER_MINUTE = 10
WINDOW_SECONDS = 60.0


class RateLimiter:
    """Не более `limit` запросов за `window` секунд с одного ключа."""

    def __init__(self, limit: int, window: float) -> None:
        """Задать лимит и длину окна."""
        self._limit = limit
        self._window = window
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Учесть запрос; `False`, если лимит исчерпан."""
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        return True


def limit_ai_requests(request: Request) -> None:
    """Зависимость: `429 rate_limited`, если IP превысил лимит AI-запросов."""
    limiter: RateLimiter = request.app.state.ai_rate_limiter
    host = request.client.host if request.client else "unknown"
    if not limiter.allow(host):
        raise ApiError(
            HTTPStatus.TOO_MANY_REQUESTS,
            "rate_limited",
            "Слишком много запросов, попробуйте через минуту",
        )
