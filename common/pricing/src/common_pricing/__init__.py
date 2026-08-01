"""common-pricing — pure calculation library for Orcha billing.

Architectural law: this package MUST NOT import prisma, redis, httpx, asyncpg,
or fastapi.  All operational side-effects live in the service that calls these functions.
"""
