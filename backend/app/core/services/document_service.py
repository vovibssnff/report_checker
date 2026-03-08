from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING

from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    CheckRuleId,
    DocumentId,
    DocumentStatus,
    DocumentType,
    Pagination,
    UserId,
    ValidationResult,
)
from app.core.ports.driving.document_querying import DocumentQueryUseCase
from app.core.ports.driving.document_uploading import DocumentUploadUseCase
from app.core.ports.driving.rule_managing import RuleManagementUseCase

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterable

    from app.core.domain.entities.check_rule import CheckRule
    from app.core.ports.driven.check_rule_repository import CheckRuleRepository
    from app.core.ports.driven.document_repository import DocumentRepository
    from app.core.ports.driven.file_storage import FileStoragePort


class DocumentService(DocumentUploadUseCase, DocumentQueryUseCase, RuleManagementUseCase):
    def __init__(
        self,
        doc_repo: DocumentRepository,
        storage: FileStoragePort,
        rule_repo: CheckRuleRepository,
        validate_pdf: Callable[[bytes], ValidationResult],
    ) -> None:
        self._doc_repo = doc_repo
        self._storage = storage
        self._rule_repo = rule_repo
        self._validate_pdf = validate_pdf

    async def upload_for_user(
        self,
        user_id: UserId,
        document_type: DocumentType,
        files: Iterable[tuple[str, bytes]],
    ) -> list[Document]:
        documents: list[Document] = []
        for filename, content in files:
            doc = await self._upload_single(
                content=content,
                filename=filename,
                document_type=document_type,
                user_id=user_id,
                source="user_upload",
            )
            documents.append(doc)
        return documents

    async def upload_internal(
        self,
        document_type: DocumentType,
        files: Iterable[tuple[str, bytes]],
        source: str,
    ) -> list[Document]:
        documents: list[Document] = []
        for filename, content in files:
            doc = await self._upload_single(
                content=content,
                filename=filename,
                document_type=document_type,
                user_id=None,
                source=source,
            )
            documents.append(doc)
        return documents

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
        return await self._doc_repo.list_for_user(
            user_id,
            document_type=document_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            pagination=pagination,
        )

    async def get_by_id(self, document_id: DocumentId) -> Document:
        return await self._doc_repo.get_by_id(document_id)

    async def delete_document(self, document_id: DocumentId) -> None:
        doc = await self._doc_repo.get_by_id(document_id)
        await self._storage.delete_file(doc.s3_key)
        await self._doc_repo.delete(document_id)

    async def get_file_bytes(self, document_id: DocumentId) -> AsyncIterator[bytes]:
        doc = await self._doc_repo.get_by_id(document_id)
        return self._storage.download_file(doc.s3_key)

    async def list_rules(
        self,
        *,
        document_type: DocumentType | None = None,
        enabled: bool | None = None,
    ) -> list[CheckRule]:
        return await self._rule_repo.list(document_type=document_type, enabled=enabled)

    async def update_rule(
        self,
        rule_id: CheckRuleId,
        *,
        enabled: bool | None = None,
        config: dict | None = None,
    ) -> CheckRule:
        rule = await self._rule_repo.get_by_id(rule_id)
        if enabled is not None:
            rule.enabled = enabled
        if config is not None:
            rule.config = config
        return await self._rule_repo.update(rule)

    async def _upload_single(
        self,
        *,
        content: bytes,
        filename: str,
        document_type: DocumentType,
        user_id: UserId | None,
        source: str,
    ) -> Document:
        validation = self._validate_pdf(content)
        if not validation.valid:
            raise ValueError(f"Invalid PDF: {validation.error}")

        doc_id = DocumentId(uuid.uuid4())
        if user_id is not None:
            s3_key = f"documents/{user_id}/{doc_id}/{filename}"
        else:
            s3_key = f"documents/internal/{doc_id}/{filename}"

        await self._storage.upload_file(s3_key, BytesIO(content), "application/pdf")

        document = Document(
            id=doc_id,
            document_type=document_type,
            filename=filename,
            s3_key=s3_key,
            file_size=len(content),
            status=DocumentStatus.PENDING,
            source=source,
            uploaded_at=datetime.now(UTC),
            checked_at=None,
            user_id=user_id,
        )
        return await self._doc_repo.create(document)
