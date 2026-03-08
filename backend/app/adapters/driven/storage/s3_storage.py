from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, BinaryIO

from aiobotocore.session import get_session

from app.config import settings
from app.core.ports.driven.file_storage import FileStoragePort

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


class S3Storage(FileStoragePort):
    def __init__(
        self,
        endpoint_url: str = settings.S3_ENDPOINT_URL,
        access_key: str = settings.S3_ACCESS_KEY,
        secret_key: str = settings.S3_SECRET_KEY,
        bucket_name: str = settings.S3_BUCKET_NAME,
        region: str = settings.S3_REGION,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket_name = bucket_name
        self._region = region
        self._session = get_session()

    @asynccontextmanager
    async def _client(self):
        async with self._session.create_client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        ) as client:
            yield client

    async def upload_file(self, key: str, data: BinaryIO, content_type: str) -> None:
        body = data.read()
        async with self._client() as client:
            await client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type,
            )

    async def download_file(self, key: str) -> AsyncGenerator[bytes]:
        async with self._client() as client:
            response = await client.get_object(Bucket=self._bucket_name, Key=key)
            stream = response["Body"]
            async for chunk in stream.iter_chunks(_CHUNK_SIZE):
                yield chunk

    async def delete_file(self, key: str) -> None:
        async with self._client() as client:
            await client.delete_object(Bucket=self._bucket_name, Key=key)

    async def file_exists(self, key: str) -> bool:
        async with self._client() as client:
            try:
                await client.head_object(Bucket=self._bucket_name, Key=key)
                return True
            except client.exceptions.ClientError:
                return False
