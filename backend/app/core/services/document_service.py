from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING

from app.checkers.pdf_parser import parse_pdf
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

        resolved_source = source
        if source == "user_upload":
            extracted_author = _extract_author_from_pdf(content)
            resolved_source = extracted_author if extracted_author else "Не указан"

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
            source=resolved_source,
            uploaded_at=datetime.now(UTC),
            checked_at=None,
            user_id=user_id,
        )
        return await self._doc_repo.create(document)


_AUTHOR_PATTERNS = [
    re.compile(
        r"(?:обучающ(?:ийся|аяся)|студент(?:ка)?|автор)\s*[:\-]\s*([А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+){1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:выполнил(?:а)?|подготовил(?:а)?)\s*[:\-]\s*([А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+){1,3})",
        re.IGNORECASE,
    ),
]


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\u00a0", " ")).strip()


def _extract_author_from_pdf(content: bytes) -> str | None:
    try:
        parsed = parse_pdf(content)
    except Exception:
        return None

    candidates: list[str] = []
    for page in parsed.pages[:2]:
        candidates.extend(page.lines[:40])

    for raw_line in candidates:
        line = _normalize_line(raw_line)
        if not line:
            continue
        for pattern in _AUTHOR_PATTERNS:
            match = pattern.search(line)
            if match:
                author = _normalize_line(match.group(1))
                # Keep DB-safe length (column currently String(30)).
                return author[:30]
    return None
