"""Small single-process login limiter for local deployments.

At multi-worker/company deployment, enforce a shared rate limit at the reverse proxy too.
Client IP comes from the ASGI server, not from an untrusted forwarded header.
"""

from collections import OrderedDict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

_failures: OrderedDict[str, deque[float]] = OrderedDict()
_lock = Lock()
WINDOW = 900
MAX_KEYS = 10000


def _keys(request: Request, identifier: str) -> tuple[str, str]:
    address = request.client.host if request.client else "unknown"
    return address, address + ":" + identifier.strip().casefold()


def _prune(key: str, now: float) -> deque[float]:
    events = _failures.setdefault(key, deque())
    while events and events[0] < now - WINDOW:
        events.popleft()
    _failures.move_to_end(key)
    while len(_failures) > MAX_KEYS:
        _failures.popitem(last=False)
    return events


def check_login_limit(request: Request, identifier: str) -> None:
    with _lock:
        now = monotonic()
        address, account = _keys(request, identifier)
        if len(_prune(address, now)) >= 30 or len(_prune(account, now)) >= 8:
            raise HTTPException(
                429,
                "Too many sign-in attempts. Try again in 15 minutes.",
                headers={"Retry-After": "900"},
            )


def record_login_failure(request: Request, identifier: str) -> None:
    with _lock:
        now = monotonic()
        for key in _keys(request, identifier):
            _prune(key, now).append(now)


def clear_account_failures(request: Request, identifier: str) -> None:
    with _lock:
        _failures.pop(_keys(request, identifier)[1], None)
