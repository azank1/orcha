"""S3 client — wraps boto3. Points to LocalStack in dev, real AWS in prod.

Configured entirely from environment via settings — no code changes between envs.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """Async-friendly boto3 wrapper for artifact storage."""

    def __init__(self) -> None:
        kwargs: dict = {
            "region_name": settings.aws_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url

        self._s3 = boto3.client("s3", **kwargs)
        self._bucket = settings.artifact_s3_bucket

    async def put_object(self, key: str, data: bytes, content_type: str) -> str:
        """Upload bytes to S3. Returns the S3 key."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            ),
        )
        return key

    async def get_object(self, key: str) -> bytes:
        """Download bytes from S3."""
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self._s3.get_object(Bucket=self._bucket, Key=key),
            )
            return response["Body"].read()
        except ClientError as exc:
            logger.error("S3 get_object failed for key %s: %s", key, exc)
            raise

    def presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed download URL."""
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


@lru_cache(maxsize=1)
def get_s3_client() -> S3Client:
    """Return the singleton S3Client (lazy-initialised)."""
    return S3Client()
