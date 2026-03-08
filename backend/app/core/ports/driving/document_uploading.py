from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.core.domain.entities.document import Document
    from app.core.domain.value_objects import DocumentType, UserId


class DocumentUploadUseCase(ABC):
    @abstractmethod
    async def upload_for_user(
        self,
        user_id: UserId,
        document_type: DocumentType,
        files: Iterable[tuple[str, bytes]],
    ) -> list[Document]:
        """
        Upload one or more documents on behalf of an authenticated user.
        Each file is a (filename, content_bytes) tuple.
        """

    @abstractmethod
    async def upload_internal(
        self,
        document_type: DocumentType,
        files: Iterable[tuple[str, bytes]],
        source: str,
    ) -> list[Document]:
        """
        Upload one or more documents from an internal university service.
        No user association, but `source` is stored for audit.
        """
