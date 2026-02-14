"""Input sanitization utilities for API endpoints."""

import logging
import re
from pathlib import PurePosixPath

logger = logging.getLogger(__name__)

# Characters not allowed in filenames
_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Max lengths
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_LENGTH = 128
MAX_FILENAME_LENGTH = 255


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and injection.

    Strips directory components, removes unsafe characters, and
    truncates to a safe length.
    """
    # Take only the basename (no directory traversal)
    name = PurePosixPath(filename).name

    # Remove any unsafe characters
    name = _UNSAFE_FILENAME_RE.sub("_", name)

    # Remove leading dots (hidden files / directory traversal)
    name = name.lstrip(".")

    # Truncate
    if len(name) > MAX_FILENAME_LENGTH:
        ext = PurePosixPath(name).suffix
        name = name[: MAX_FILENAME_LENGTH - len(ext)] + ext

    # Fallback if empty
    if not name:
        name = "upload"

    return name


def validate_email_input(email: str) -> str:
    """Validate and sanitize email input.

    Pydantic's EmailStr handles format validation; this adds
    length checking and whitespace stripping.
    """
    email = email.strip()

    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(f"Email must be at most {MAX_EMAIL_LENGTH} characters")

    return email


def validate_password_input(password: str) -> str:
    """Validate password input.

    Enforces minimum and maximum length. Does NOT strip whitespace
    since spaces can be valid password characters.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters")

    return password


def sanitize_content_type(content_type: str | None) -> str:
    """Sanitize and normalize a content type string."""
    if not content_type:
        return ""
    # Take only the MIME type, strip parameters
    return content_type.split(";")[0].strip().lower()
