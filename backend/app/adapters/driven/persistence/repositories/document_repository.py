from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select

from app.adapters.driven.persistence.database.models.check_result import CheckResultModel
from app.adapters.driven.persistence.database.models.document import DocumentModel
from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    DocumentId,
    DocumentStatus,
    DocumentType,
    Pagination,
    UserId,
)
from app.core.ports.driven.document_repository import DocumentRepository

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession


class PgDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        model = self._entity_to_model(document)
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def update(self, document: Document) -> Document:
        model = await self._session.get(DocumentModel, document.id)
        if model is None:
            raise ValueError(f"Document {document.id} not found")
        model.document_type = document.document_type.value
        model.filename = document.filename
        model.s3_key = document.s3_key
        model.file_size = document.file_size
        model.status = document.status.value
        model.source = document.source
        model.uploaded_at = document.uploaded_at
        model.checked_at = document.checked_at
        model.user_id = document.user_id
        model.page_count = document.page_count
        await self._session.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, document_id: DocumentId) -> Document:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            raise ValueError(f"Document {document_id} not found")
        return self._model_to_entity(model)

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
        stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)

        if document_type is not None:
            stmt = stmt.where(DocumentModel.document_type == document_type.value)
        if status is not None:
            stmt = stmt.where(DocumentModel.status == status.value)
        if date_from is not None:
            stmt = stmt.where(DocumentModel.uploaded_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(DocumentModel.uploaded_at <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(DocumentModel.uploaded_at.desc())

        if pagination is not None:
            offset = (pagination.page - 1) * pagination.size
            stmt = stmt.offset(offset).limit(pagination.size)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models], total

    async def delete(self, document_id: DocumentId) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model is None:
            raise ValueError(f"Document {document_id} not found")
        await self._session.execute(delete(CheckResultModel).where(CheckResultModel.document_id == document_id))
        await self._session.delete(model)
        await self._session.flush()

    @staticmethod
    def _entity_to_model(entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            document_type=entity.document_type.value,
            filename=entity.filename,
            s3_key=entity.s3_key,
            file_size=entity.file_size,
            status=entity.status.value,
            source=entity.source,
            uploaded_at=entity.uploaded_at,
            checked_at=entity.checked_at,
            user_id=entity.user_id,
            page_count=entity.page_count,
        )

    @staticmethod
    def _model_to_entity(model: DocumentModel) -> Document:
        return Document(
            id=DocumentId(model.id),
            document_type=DocumentType(model.document_type),
            filename=model.filename,
            s3_key=model.s3_key,
            file_size=model.file_size,
            status=DocumentStatus(model.status),
            source=model.source,
            uploaded_at=model.uploaded_at,
            checked_at=model.checked_at,
            user_id=UserId(model.user_id) if model.user_id else None,
            page_count=model.page_count,
        )
