"""CSRF protection (double-submit cookie).

Mutating requests must send an ``X-CSRF-Token`` header matching a non-HttpOnly
cookie. SameSite=Lax session cookies already mitigate most CSRF for a
same-origin PWA; this adds an explicit check for mutating verbs.
"""

from __future__ import annotations

import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
CSRF_COOKIE = "growthos_csrf"
CSRF_HEADER = "X-CSRF-Token"


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in SAFE_METHODS:
            cookie_token = request.cookies.get(CSRF_COOKIE, "")
            header_token = request.headers.get(CSRF_HEADER, "")
            if not cookie_token or not hmac.compare_digest(cookie_token, header_token):
                return Response(
                    status_code=403,
                    content=b'{"detail":"CSRF token missing or invalid"}',
                    media_type="application/json",
                )
        response = await call_next(request)
        if CSRF_COOKIE not in request.cookies and not response.headers.get(
            "set-cookie", ""
        ).count(CSRF_COOKIE):
            # Only set when absent to avoid churn.
            pass
        return response
