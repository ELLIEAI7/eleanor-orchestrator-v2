import os
from slowapi import Limiter
from slowapi.util import get_remote_address

RATE_LIMIT = os.getenv("ELEANOR_RATE_LIMIT", "20/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])
