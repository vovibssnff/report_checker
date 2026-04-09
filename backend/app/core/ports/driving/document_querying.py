from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime

    from app.core.domain.entities.document import Document
    from app.core.domain.value_objects import DocumentId, DocumentStatus, DocumentType, Pagination, UserId


class DocumentQueryUseCase(ABC):
    @abstractmethod
    async def list_for_user(
        self,
        user_id: UserId,
        *,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        pagination: Pagination | None = None,
    ) -> tuple[list[Document], int]:
        """Return a page of documents for a user and the total count."""

    @abstractmethod
    async def list_all(
        self,
        *,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        pagination: Pagination | None = None,
    ) -> tuple[list[Document], int]:
        """Return a page of documents for all users and the total count."""

    @abstractmethod
    async def get_by_id(self, document_id: DocumentId) -> Document:
        """Return a single document by id or raise."""

    @abstractmethod
    async def delete_document(self, document_id: DocumentId) -> None:
        """Delete a document and its S3 object."""

    @abstractmethod
    async def get_file_bytes(self, document_id: DocumentId) -> AsyncIterator[bytes]:
        """Stream original PDF bytes from storage."""
