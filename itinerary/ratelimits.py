import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

_RATE_RE = re.compile(r"^(\d+)/(s|m|h|d)$")
_PERIOD_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def ratelimit_response(request, *, as_json: bool = False):
    message = "Rate limit exceeded. Try again later."
    if as_json:
        return JsonResponse({"detail": message}, status=429)
    return HttpResponse(message, status=429)


def enforce_ai_rate_limit(request) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    if not request.user.is_authenticated:
        return True
    match = _RATE_RE.match(getattr(settings, "AI_RATE_LIMIT", "10/h"))
    if not match:
        return True
    allowed, period = int(match.group(1)), match.group(2)
    key = f"ai-rate-limit:{request.user.pk}"
    current = cache.get(key, 0)
    if current >= allowed:
        return False
    cache.set(key, current + 1, _PERIOD_SECONDS[period])
    return True
