"""S3 client for Gateway — mirrors SuperAgent's s3_client.py pattern."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)


class S3Client:
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
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


@lru_cache(maxsize=1)
def get_s3_client() -> S3Client:
    return S3Client()
