from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    DocumentId,
    DocumentStatus,
    DocumentType,
    Pagination,
)

if TYPE_CHECKING:
    from app.adapters.driven.persistence.repositories.document_repository import (
        PgDocumentRepository,
    )
    from app.core.domain.entities.user import User

pytestmark = pytest.mark.integration


async def test_create_and_get_document(doc_repo: PgDocumentRepository, test_user: User):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="test.pdf",
        s3_key=f"documents/{test_user.id}/{doc_id}/test.pdf",
        file_size=4096,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )

    created = await doc_repo.create(doc)
    assert created.id == doc_id
    assert created.filename == "test.pdf"

    fetched = await doc_repo.get_by_id(doc_id)
    assert fetched.id == doc_id
    assert fetched.document_type == DocumentType.VKR_TEMPLATE
    assert fetched.user_id == test_user.id


async def test_update_document_status(doc_repo: PgDocumentRepository, test_user: User):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.PRACTICE_REPORT,
        filename="update_me.pdf",
        s3_key=f"documents/{test_user.id}/{doc_id}/update_me.pdf",
        file_size=2048,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )
    await doc_repo.create(doc)

    doc.status = DocumentStatus.CHECKING
    updated = await doc_repo.update(doc)
    assert updated.status == DocumentStatus.CHECKING

    doc.status = DocumentStatus.PASSED
    doc.checked_at = datetime.now(UTC)
    updated = await doc_repo.update(doc)
    assert updated.status == DocumentStatus.PASSED
    assert updated.checked_at is not None


async def test_list_for_user(doc_repo: PgDocumentRepository, test_user: User):
    for i in range(3):
        doc = Document(
            id=DocumentId(uuid.uuid4()),
            document_type=DocumentType.VKR_TEMPLATE,
            filename=f"file_{i}.pdf",
            s3_key=f"documents/{test_user.id}/file_{i}.pdf",
            file_size=1000 + i,
            status=DocumentStatus.PENDING,
            source="user_upload",
            uploaded_at=datetime.now(UTC),
            checked_at=None,
            user_id=test_user.id,
        )
        await doc_repo.create(doc)

    docs, total = await doc_repo.list_for_user(test_user.id)
    assert total >= 3
    assert all(d.user_id == test_user.id for d in docs)


async def test_list_with_pagination(doc_repo: PgDocumentRepository, test_user: User):
    for i in range(5):
        await doc_repo.create(
            Document(
                id=DocumentId(uuid.uuid4()),
                document_type=DocumentType.VKR_TEMPLATE,
                filename=f"page_{i}.pdf",
                s3_key=f"documents/{test_user.id}/page_{i}.pdf",
                file_size=500,
                status=DocumentStatus.PENDING,
                source="user_upload",
                uploaded_at=datetime.now(UTC),
                checked_at=None,
                user_id=test_user.id,
            )
        )

    page1, total = await doc_repo.list_for_user(test_user.id, pagination=Pagination(page=1, size=2))
    assert len(page1) == 2
    assert total >= 5


async def test_delete_document(doc_repo: PgDocumentRepository, test_user: User):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="delete_me.pdf",
        s3_key=f"documents/{test_user.id}/{doc_id}/delete_me.pdf",
        file_size=512,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )
    await doc_repo.create(doc)

    await doc_repo.delete(doc_id)

    with pytest.raises(ValueError, match="not found"):
        await doc_repo.get_by_id(doc_id)


async def test_get_nonexistent_raises(doc_repo: PgDocumentRepository):
    with pytest.raises(ValueError, match="not found"):
        await doc_repo.get_by_id(DocumentId(uuid.uuid4()))
