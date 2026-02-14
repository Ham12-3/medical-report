"""In-memory rate limiter for upload endpoints.

Uses a sliding window approach: tracks timestamps of recent uploads
per user and rejects requests that exceed the configured limit.
"""

import logging
import time
from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

# Store: user_id -> list of upload timestamps
_upload_timestamps: dict[str, list[float]] = defaultdict(list)

WINDOW_SECONDS = 3600  # 1 hour


def check_upload_rate_limit(user_id: UUID) -> None:
    """Raise HTTP 429 if the user has exceeded the upload rate limit.

    Cleans up expired timestamps on each check.
    """
    uid = str(user_id)
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # Remove expired entries
    _upload_timestamps[uid] = [
        ts for ts in _upload_timestamps[uid] if ts > cutoff
    ]

    if len(_upload_timestamps[uid]) >= settings.upload_rate_limit:
        oldest = _upload_timestamps[uid][0]
        retry_after = int(oldest + WINDOW_SECONDS - now) + 1
        logger.warning(
            "Rate limit exceeded for user %s: %d uploads in the last hour",
            uid,
            len(_upload_timestamps[uid]),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Upload rate limit exceeded. Maximum {settings.upload_rate_limit} "
                f"uploads per hour. Try again in {retry_after} seconds."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    # Record this upload
    _upload_timestamps[uid].append(now)
