"""Authentication utilities for PAT token management."""

import bcrypt


def hash_pat_token(token: str) -> str:
    """
    Hash a PAT token using bcrypt.

    Args:
        token: The PAT token to hash

    Returns:
        The bcrypt hash as a string
    """
    return bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()


def verify_pat_token(token: str, hashed: str) -> bool:
    """
    Verify a PAT token against its hash.

    Args:
        token: The plain PAT token
        hashed: The bcrypt hash

    Returns:
        True if the token matches, False otherwise
    """
    try:
        return bcrypt.checkpw(token.encode(), hashed.encode())
    except Exception:
        return False


def validate_pat_token_format(token: str) -> bool:
    """
    Validate PAT token format.

    Format: metaorcha_pat_<40 chars total>

    Args:
        token: The token to validate

    Returns:
        True if format is valid, False otherwise
    """
    if not token:
        return False

    if not token.startswith("metaorcha_pat_"):
        return False

    return len(token) == 40
