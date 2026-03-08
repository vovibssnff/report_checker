from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class FileStoragePort(ABC):
    @abstractmethod
    async def upload_file(self, key: str, data: BinaryIO, content_type: str) -> None: ...

    @abstractmethod
    def download_file(self, key: str) -> AsyncGenerator[bytes]: ...

    @abstractmethod
    async def delete_file(self, key: str) -> None: ...

    @abstractmethod
    async def file_exists(self, key: str) -> bool: ...
