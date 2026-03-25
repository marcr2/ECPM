"""Rate limiting configuration using SlowAPI.

Tiers:
- Read endpoints: 100/minute
- Write endpoints: 10/minute
- Training: 5/hour
- Auth token: 5/minute (brute-force protection)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=None,  # in-memory by default; set to Redis URI at app startup
)

RATE_READ = "100/minute"
RATE_WRITE = "10/minute"
RATE_TRAINING = "5/hour"
RATE_AUTH = "5/minute"
