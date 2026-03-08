from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.core.domain.entities.check_rule import CheckRule
from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    CheckRuleId,
    DocumentId,
    DocumentStatus,
    DocumentType,
    UserId,
)
from app.core.services.document_service import DocumentService, ValidationResult


@pytest.fixture()
def doc_repo():
    repo = AsyncMock()
    repo.create = AsyncMock(side_effect=lambda d: d)
    repo.get_by_id = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_for_user = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture()
def storage():
    s = AsyncMock()
    s.upload_file = AsyncMock()
    s.delete_file = AsyncMock()
    s.download_file = Mock()
    return s


@pytest.fixture()
def rule_repo():
    repo = AsyncMock()
    repo.list = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock(side_effect=lambda r: r)
    return repo


@pytest.fixture()
def validate_pdf_ok():
    return MagicMock(return_value=ValidationResult(valid=True))


@pytest.fixture()
def validate_pdf_fail():
    return MagicMock(return_value=ValidationResult(valid=False, error="bad pdf"))


@pytest.fixture()
def service(doc_repo, storage, rule_repo, validate_pdf_ok):
    return DocumentService(
        doc_repo=doc_repo,
        storage=storage,
        rule_repo=rule_repo,
        validate_pdf=validate_pdf_ok,
    )


def _make_document(
    user_id: UserId | None = None,
    status: DocumentStatus = DocumentStatus.PENDING,
) -> Document:
    return Document(
        id=DocumentId(uuid.uuid4()),
        document_type=DocumentType.VKR_TEMPLATE,
        filename="test.pdf",
        s3_key="documents/test/test.pdf",
        file_size=1024,
        status=status,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=user_id,
    )


class TestUploadForUser:
    @pytest.mark.asyncio
    async def test_calls_validate_and_stores(self, service, doc_repo, storage, validate_pdf_ok):
        user_id = UserId(uuid.uuid4())
        content = b"fake-pdf"
        files = [("report.pdf", content)]

        docs = await service.upload_for_user(user_id, DocumentType.VKR_TEMPLATE, files)

        validate_pdf_ok.assert_called_once_with(content)
        storage.upload_file.assert_awaited_once()
        doc_repo.create.assert_awaited_once()
        assert len(docs) == 1
        assert docs[0].user_id == user_id
        assert docs[0].status == DocumentStatus.PENDING

    @pytest.mark.asyncio
    async def test_multiple_files(self, service, doc_repo, storage, validate_pdf_ok):
        user_id = UserId(uuid.uuid4())
        files = [("a.pdf", b"aaa"), ("b.pdf", b"bbb")]

        docs = await service.upload_for_user(user_id, DocumentType.VKR_TEMPLATE, files)

        assert len(docs) == 2
        assert validate_pdf_ok.call_count == 2
        assert storage.upload_file.await_count == 2
        assert doc_repo.create.await_count == 2

    @pytest.mark.asyncio
    async def test_invalid_pdf_raises(self, doc_repo, storage, rule_repo, validate_pdf_fail):
        svc = DocumentService(
            doc_repo=doc_repo,
            storage=storage,
            rule_repo=rule_repo,
            validate_pdf=validate_pdf_fail,
        )
        user_id = UserId(uuid.uuid4())

        with pytest.raises(ValueError, match="Invalid PDF"):
            await svc.upload_for_user(user_id, DocumentType.VKR_TEMPLATE, [("f.pdf", b"x")])

        storage.upload_file.assert_not_awaited()
        doc_repo.create.assert_not_awaited()


class TestUploadInternal:
    @pytest.mark.asyncio
    async def test_user_id_is_none(self, service, doc_repo, storage):
        docs = await service.upload_internal(
            DocumentType.VKR_TEMPLATE,
            [("internal.pdf", b"data")],
            source="api",
        )

        assert len(docs) == 1
        assert docs[0].user_id is None
        assert docs[0].source == "api"
        assert "internal" in docs[0].s3_key


class TestListForUser:
    @pytest.mark.asyncio
    async def test_delegates_to_repo(self, service, doc_repo):
        user_id = UserId(uuid.uuid4())
        expected = ([_make_document(user_id)], 1)
        doc_repo.list_for_user.return_value = expected

        result = await service.list_for_user(user_id)

        doc_repo.list_for_user.assert_awaited_once()
        assert result == expected


class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_deletes_storage_and_repo(self, service, doc_repo, storage):
        doc = _make_document()
        doc_repo.get_by_id.return_value = doc

        await service.delete_document(doc.id)

        storage.delete_file.assert_awaited_once_with(doc.s3_key)
        doc_repo.delete.assert_awaited_once_with(doc.id)


class TestGetFileBytes:
    @pytest.mark.asyncio
    async def test_delegates(self, service, doc_repo, storage):
        doc = _make_document()
        doc_repo.get_by_id.return_value = doc
        sentinel = object()
        storage.download_file.return_value = sentinel

        result = await service.get_file_bytes(doc.id)

        storage.download_file.assert_called_once_with(doc.s3_key)
        assert result is sentinel


class TestListRules:
    @pytest.mark.asyncio
    async def test_delegates_to_rule_repo(self, service, rule_repo):
        rules = [
            CheckRule(
                id=CheckRuleId(uuid.uuid4()),
                code="vkr.fmt",
                document_type=DocumentType.VKR_TEMPLATE,
                name="Font",
                description="",
                enabled=True,
                config=None,
            )
        ]
        rule_repo.list.return_value = rules

        result = await service.list_rules(document_type=DocumentType.VKR_TEMPLATE)

        rule_repo.list.assert_awaited_once_with(document_type=DocumentType.VKR_TEMPLATE, enabled=None)
        assert result == rules


class TestUpdateRule:
    @pytest.mark.asyncio
    async def test_updates_enabled(self, service, rule_repo):
        rule = CheckRule(
            id=CheckRuleId(uuid.uuid4()),
            code="vkr.fmt",
            document_type=DocumentType.VKR_TEMPLATE,
            name="Font",
            description="",
            enabled=True,
            config=None,
        )
        rule_repo.get_by_id.return_value = rule

        result = await service.update_rule(rule.id, enabled=False)

        assert result.enabled is False
        rule_repo.update.assert_awaited_once()
