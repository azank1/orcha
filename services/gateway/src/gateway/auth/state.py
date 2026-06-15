"""HMAC-signed, URL-safe base64 state encoding for OAuth flows.

The `state` parameter in OAuth authorization URLs is a critical SSRF / CSRF
prevention mechanism.  It must be:
    1. Tamper-proof    — HMAC-SHA256 signature bound to a secret.
    2. Opaque to IdPs  — base64url encoded.
    3. Stateless       — all context embedded; no server-side session needed.

Encoding:
    payload_json  →  base64url(payload_json) + "." + base64url(HMAC-SHA256(encoded_payload))

Decoding verifies the HMAC before parsing the payload, preventing forgery.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json


class StateError(Exception):
    """Raised when a state token is malformed or the HMAC signature is invalid."""


def encode_state(payload: dict, secret: str) -> str:
    """Encode a dict payload as a URL-safe, HMAC-signed state token.

    Args:
        payload: Arbitrary JSON-serialisable dict to embed.
        secret:  HMAC signing secret (should be ≥ 32 random bytes).

    Returns:
        ``{b64url_payload}.{b64url_sig}`` string safe for use as an OAuth `state`.
    """
    encoded_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=")

    sig = hmac.new(
        secret.encode(),
        encoded_payload,
        hashlib.sha256,
    ).digest()
    encoded_sig = base64.urlsafe_b64encode(sig).rstrip(b"=")

    return f"{encoded_payload.decode()}.{encoded_sig.decode()}"


def decode_and_verify_state(state: str, secret: str) -> dict:
    """Verify the HMAC signature and return the decoded payload dict.

    Args:
        state:  Token produced by :func:`encode_state`.
        secret: The same secret used during encoding.

    Returns:
        Decoded payload dict.

    Raises:
        StateError: If the token is malformed or the signature is invalid.
    """
    parts = state.split(".", 1)
    if len(parts) != 2:
        raise StateError("Malformed state token: missing signature segment")

    encoded_payload, encoded_sig = parts

    # Re-add padding stripped during encoding
    def _pad(s: str) -> str:
        return s + "=" * (-len(s) % 4)

    try:
        payload_bytes = base64.urlsafe_b64decode(_pad(encoded_payload))
        provided_sig = base64.urlsafe_b64decode(_pad(encoded_sig))
    except Exception as exc:
        raise StateError(
            f"Malformed state token: base64 decode failed — {exc}"
        ) from exc

    expected_sig = hmac.new(
        secret.encode(),
        encoded_payload.encode(),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise StateError(
            "State token signature is invalid — possible CSRF or tampering"
        )

    try:
        return json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise StateError(
            f"Malformed state token: payload is not valid JSON — {exc}"
        ) from exc
