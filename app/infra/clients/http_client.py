from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class RetryPolicy:
    max_retries: int = 2
    base_delay: float = 0.5
    max_delay: float = 4.0


class RateLimiter:
    def __init__(self, min_interval: float = 1.0) -> None:
        self._min_interval = min_interval
        self._last_request = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()


class HttpClient:
    def __init__(
        self,
        *,
        timeout: float = 10.0,
        retry_policy: RetryPolicy | None = None,
        min_interval: float = 1.0,
    ) -> None:
        self._client = httpx.Client(timeout=timeout)
        self._retry = retry_policy or RetryPolicy()
        self._rate_limiter = RateLimiter(min_interval=min_interval)

    def get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return self._request("GET", url, params=params)

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self._request("POST", url, json=json, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._retry.max_retries + 1):
            self._rate_limiter.wait()
            try:
                response = self._client.request(
                    method, url, params=params, json=json, headers=headers
                )
                if response.status_code in {429, 500, 502, 503, 504}:
                    self._sleep_retry(response, attempt)
                    continue
                response.raise_for_status()
                return response
            except Exception as exc:  # pragma: no cover - network path
                last_exc = exc
                self._sleep_retry(None, attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed without exception")

    def _sleep_retry(self, response: httpx.Response | None, attempt: int) -> None:
        if attempt >= self._retry.max_retries:
            return
        delay = min(self._retry.base_delay * (2**attempt), self._retry.max_delay)
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                delay = max(delay, float(retry_after))
        time.sleep(delay)

    def close(self) -> None:
        self._client.close()
