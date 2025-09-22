from __future__ import annotations
from abc import ABC, abstractmethod
import base64
import json
import os
from typing import Optional, Dict, Any
import jwt as _pyjwt
from models.base.agent import Agent, Vendor
from dotenv import load_dotenv

load_dotenv()


JWT_SECRET = os.getenv('JWT_SECRET', 'hello123')

def _b64url_encode(data: bytes) -> str:
    """Base64-url encode without padding (RFC 7515 style)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


class AuthResolver:
    def __init__(self, agent: Agent):
        self.agent = agent

    def resolve(self) -> AuthService:
        if self.agent.vendor == Vendor.foodtec:
            if not self.agent.credentials.get(
                "username"
            ) or not self.agent.credentials.get("password"):
                raise ValueError(
                    "Foodtec BasicAuth requires 'username' and 'password' in credentials."
                )

            self._auth = BasicAuth(
                username=self.agent.credentials.get("username"),
                password=self.agent.credentials.get("password"),
            )
            return self._auth
        elif self.agent.vendor == Vendor.restarage:
            if not self.agent.credentials.get("token"):
                raise ValueError("Restarage JWTAuth requires 'token' in credentials.")

            self._auth = JWTAuth(token=self.agent.credentials.get("token"))
            return self._auth
        else:
            raise NotImplementedError(
                f"AuthService for vendor {self.agent.vendor} is not implemented"
            )


class AuthService(ABC):
    """Abstract authentication provider.

    Subclasses must implement `get_auth()` and return the full Authorization header value
    (for example: 'Basic <token>' or 'Bearer <token>').
    """

    @abstractmethod
    def get_auth(self) -> str:  # pragma: no cover - interface
        raise NotImplementedError()


class BasicAuth(AuthService):
    """Basic authentication provider.

    Accepts either:
      - an already-encoded token (base64 string) via `token`, or
      - a `username` and `password` (which will be joined with ':' and base64-encoded), or
      - a `credentials` string in the form 'username:password'.

    Example:
        BasicAuth(token='QWxhZGRpbjpvcGVuIHNlc2FtZQ==')
        BasicAuth(username='user', password='pass')
        BasicAuth(credentials='user:pass')
    """

    def __init__(
        self,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        credentials: Optional[str] = None,
    ) -> None:
        if token:
            self._token = token
        else:
            cred: Optional[str] = None
            if credentials:
                cred = credentials
            elif username is not None and password is not None:
                cred = f"{username}:{password}"

            if cred is None:
                raise ValueError(
                    "BasicAuth requires either 'token' or 'username'+'password' or 'credentials'."
                )

            # Encode the username:password string to base64
            token_bytes = cred.encode("utf-8")
            self._token = base64.b64encode(token_bytes).decode("ascii")

    def get_auth(self) -> str:
        """Return a full Authorization header value for Basic auth."""
        return f"Basic {self._token}"


class JWTAuth(AuthService):
    """JWT (Bearer) authentication provider.

    Accepts either:
      - an already-built JWT string via `token`, or
      - a `payload` dictionary which will be encoded into a JWT. If `key` is provided
        and the optional PyJWT library is available, the JWT will be signed using
        the provided `algorithm` (default 'HS256'). If `key` is not provided or
        PyJWT is not available, an unsigned JWT (alg='none') will be produced.

    Example:
        JWTAuth(token='eyJ...')
        JWTAuth(payload={'sub': '123'}, key='secret', algorithm='HS256')
    """

    def __init__(
        self,
        token: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        key: Optional[str] = JWT_SECRET,
        algorithm: str = "HS256",
    ) -> None:
        # Allow callers to provide a full Authorization header value like
        # 'Bearer <token>' — strip the prefix if present (case-insensitive).
        if token and isinstance(token, str) and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]

        if token and payload:
            raise ValueError("Provide either 'token' or 'payload', not both.")

        if token:
            self._token = token
        elif payload is not None:
            # If PyJWT is available and a key is provided, produce a signed JWT.
            if key and _pyjwt is not None:
                # PyJWT may return a str in modern versions
                self._token = _pyjwt.encode(payload, key, algorithm=algorithm)
                if isinstance(self._token, bytes):
                    self._token = self._token.decode("ascii")
            else:
                # produce an unsigned JWT (alg='none') by base64url-encoding header and payload
                header = {"alg": "none", "typ": "JWT"}
                header_b64 = _b64url_encode(
                    json.dumps(header, separators=(",", ":")).encode("utf-8")
                )
                payload_b64 = _b64url_encode(
                    json.dumps(payload, separators=(",", ":")).encode("utf-8")
                )
                # per RFC7515 an 'alg' of none implies no signature; some systems expect three parts
                self._token = f"{header_b64}.{payload_b64}."
        else:
            raise ValueError("JWTAuth requires either 'token' or 'payload'.")

    def get_auth(self) -> str:
        """Return a full Authorization header value for Bearer (JWT) auth."""
        return f"Bearer {self._token}"

    def get_payload(self) -> Dict[str, Any]:
        """Return the decoded JWT payload as a dict.

        - If PyJWT is available, use `decode` without verification if no key was used to sign.
        - Otherwise, perform a base64-url decode of the payload segment and parse JSON.
        """
        # If PyJWT was used to create a signed token and is available, try to decode
        if _pyjwt is not None:
            try:
                # try decode without verification (caller should verify if needed)
                # PyJWT 2.x: options={'verify_signature': False}
                return _pyjwt.decode(self._token, options={"verify_signature": False})
            except Exception:
                # fallback to manual decode below
                pass

        # Manual decode: split token into parts header.payload.signature
        parts = (self._token or "").split(".")
        if len(parts) < 2:
            raise ValueError("Invalid JWT token format")

        payload_b64 = parts[1]
        # add padding
        padding = "=" * (-len(payload_b64) % 4)
        payload_b64_padded = payload_b64 + padding
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64_padded.encode("ascii"))
            return json.loads(payload_bytes)
        except Exception as exc:
            raise ValueError(f"Failed to decode JWT payload: {exc}") from exc


__all__ = ["AuthService", "BasicAuth", "JWTAuth"]


class AgentAuth(JWTAuth):
    """JWTAuth subclass that can return an `Agent` object decoded from the JWT payload.

    The JWT payload is expected to contain the fields required by `models.base.agent.Agent`.
    """

    def get_agent(self) -> Agent:
        """Decode the JWT payload and return an `Agent` instance.

        Raises:
            ValueError: if the payload cannot be decoded or does not validate as an Agent.
        """
        payload = self.get_payload()
        try:
            return Agent.parse_obj(payload)
        except Exception as exc:
            raise ValueError(
                f"Failed to construct Agent from JWT payload: {exc}"
            ) from exc


__all__.append("AgentAuth")
