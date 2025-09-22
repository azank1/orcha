#!/usr/bin/env python3
"""
Create a JWT for an Agent object from command line arguments.

Usage examples:
  # Foodtec vendor (username/password credentials)
  python scripts/make_agent_jwt.py --name "Alice" --role "operator" --vendor foodtec --username alice --password s3cret

  # Restarage vendor (token credential)
  python scripts/make_agent_jwt.py --name "Bob" --role "agent" --vendor restarage --token "my-token-here"

The script reads `JWT_SECRET` from a `.env` file (if python-dotenv is installed) or from the environment. It prints the resulting JWT to stdout.
"""

import os
import json
import argparse
import sys
from typing import Dict, Any
from models.base.agent import Agent

# Try to use PyJWT if available
try:
    import jwt as pyjwt

    _HAS_PYJWT = True
except Exception:
    pyjwt = None
    _HAS_PYJWT = False

# Try to load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def build_agent_payload(args: argparse.Namespace) -> Dict[str, Any]:
    vendor = args.vendor
    credentials = {}
    if vendor.lower() == "foodtec":
        if not args.username or not args.password:
            raise ValueError(
                "For vendor 'foodtec' you must provide --username and --password"
            )
        credentials = {"username": args.username, "password": args.password}
    else:
        # restarage or other vendors take a token
        if not args.token:
            raise ValueError("For non-foodtec vendors you must provide --token")
        credentials = {"token": args.token}

    agent_data = {
        "name": args.name,
        "role": args.role,
        "platform": args.platform,
        "vendor": vendor,
        "credentials": credentials,
    }

    # Optional fields
    if args.store_id:
        agent_data["storeId"] = args.store_id
    if args.extra:
        try:
            extra = json.loads(args.extra)
            agent_data.setdefault("meta", {}).update(extra)
        except Exception as exc:
            raise ValueError(f"--extra must be valid JSON: {exc}") from exc

    # Validate with Agent model
    try:
        agent = Agent(**agent_data)
        return agent.model_dump()
    except Exception as exc:
        raise ValueError(f"Agent validation failed: {exc}") from exc


def encode_jwt(payload: Dict[str, Any], secret: str, alg: str = "HS256") -> str:
    if not _HAS_PYJWT or pyjwt is None:
        raise RuntimeError(
            "PyJWT is required to create JWT tokens. Install it with 'pip install PyJWT'"
        )

    # Type-checkers may not know pyjwt was successfully imported; call encode safely.
    token = pyjwt.encode(payload, secret, algorithm=alg)
    return token


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Create an Agent JWT from command line arguments"
    )
    parser.add_argument("--name", default="Mark", help="Agent name (default: Mark)")
    parser.add_argument(
        "--role", default="menuHelper", help="Agent role (default: menuHelper)"
    )
    parser.add_argument(
        "--platform",
        default="n8n",
        help="Platform where agent is deployed (default: n8n)",
    )
    parser.add_argument(
        "--vendor", default="foodtec", help="Vendor name (default: foodtec)"
    )
    parser.add_argument(
        "--username",
        default="apiclient",
        help="Username (default: apiclient for foodtec)",
    )
    parser.add_argument(
        "--password",
        default="Tn2dtS6n4u5eVYk",
        help="Password (default: Tn2dtS6n4u5eVYk for foodtec)",
    )
    parser.add_argument("--token", help="Token (for other vendors)")
    parser.add_argument("--store-id", dest="store_id", help="Optional store identifier")
    parser.add_argument(
        "--extra", help="Optional JSON string with extra meta to merge into agent.meta"
    )
    parser.add_argument(
        "--secret",
        help="Override JWT secret (otherwise read from JWT_SECRET env or .env)",
    )
    args = parser.parse_args(argv)

    secret = args.secret or os.environ.get("JWT_SECRET")
    if not secret:
        print(
            "ERROR: JWT secret not found. Set JWT_SECRET in environment or pass --secret.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        payload = build_agent_payload(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        token = encode_jwt(payload, secret)
    except Exception as exc:
        print(f"ERROR encoding JWT: {exc}", file=sys.stderr)
        sys.exit(2)

    # PyJWT >=2 returns a str; earlier versions may return bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    print(token)


if __name__ == "__main__":
    main()
