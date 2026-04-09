from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from app.core.domain.entities.document import Document
    from app.core.domain.value_objects import DocumentId, DocumentStatus, DocumentType, Pagination, UserId


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document: ...

    @abstractmethod
    async def update(self, document: Document) -> Document: ...

    @abstractmethod
    async def get_by_id(self, document_id: DocumentId) -> Document: ...

    @abstractmethod
    async def delete(self, document_id: DocumentId) -> None: ...

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
    ) -> tuple[list[Document], int]: ...

    @abstractmethod
    async def list_all(
        self,
        *,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        pagination: Pagination | None = None,
    ) -> tuple[list[Document], int]: ...
