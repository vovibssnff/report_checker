from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.checkers.base import RuleResult
from app.checkers.engine import CheckOutput
from app.core.domain.entities.check_result import CheckResult
from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    CheckResultId,
    CheckStatus,
    DocumentId,
    DocumentStatus,
    DocumentType,
    Severity,
    UserId,
)
from app.core.services.check_service import CheckService


def _make_document(
    status: DocumentStatus = DocumentStatus.PENDING,
) -> Document:
    return Document(
        id=DocumentId(uuid.uuid4()),
        document_type=DocumentType.VKR_TEMPLATE,
        filename="test.pdf",
        s3_key="documents/test.pdf",
        file_size=1024,
        status=status,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=UserId(uuid.uuid4()),
    )


@pytest.fixture()
def doc_repo():
    repo = AsyncMock()
    repo.update = AsyncMock(side_effect=lambda d: d)
    return repo


@pytest.fixture()
def check_result_repo():
    repo = AsyncMock()
    repo.replace_for_document = AsyncMock(side_effect=lambda _doc_id, results: list(results))
    repo.list_for_document = AsyncMock(return_value=[])
    return repo


@pytest.fixture()
def storage():
    s = AsyncMock()
    return s


@pytest.fixture()
def checker_engine():
    return AsyncMock()


@pytest.fixture()
def service(doc_repo, check_result_repo, storage, checker_engine):
    return CheckService(
        doc_repo=doc_repo,
        check_result_repo=check_result_repo,
        storage=storage,
        checker_engine=checker_engine,
    )


async def _async_iter(chunks: list[bytes]):
    for chunk in chunks:
        yield chunk


class TestRunChecksForDocument:
    @pytest.mark.asyncio
    async def test_all_passed(self, service, doc_repo, check_result_repo, storage, checker_engine):
        doc = _make_document()
        doc_repo.get_by_id = AsyncMock(return_value=doc)
        storage.download_file = Mock(return_value=_async_iter([b"pdf-bytes"]))
        checker_engine.run_checks = AsyncMock(
            return_value=(
                [
                    CheckOutput(
                        rule_code="vkr.fmt.page_size",
                        rule_name="Page size",
                        severity=Severity.ERROR,
                        results=[RuleResult(status=CheckStatus.PASSED, message="OK")],
                    ),
                ],
                5,
            )
        )

        results = await service.run_checks_for_document(doc.id)

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert doc.status == DocumentStatus.PASSED
        assert doc.page_count == 5
        check_result_repo.replace_for_document.assert_awaited_once()
        assert doc_repo.update.await_count == 2

    @pytest.mark.asyncio
    async def test_has_error_sets_failed(self, service, doc_repo, storage, checker_engine):
        doc = _make_document()
        doc_repo.get_by_id = AsyncMock(return_value=doc)
        storage.download_file = Mock(return_value=_async_iter([b"pdf"]))
        checker_engine.run_checks = AsyncMock(
            return_value=(
                [
                    CheckOutput(
                        rule_code="vkr.fmt.font",
                        rule_name="Font",
                        severity=Severity.ERROR,
                        results=[RuleResult(status=CheckStatus.FAILED, message="Wrong font")],
                    ),
                ],
                3,
            )
        )

        results = await service.run_checks_for_document(doc.id)

        assert doc.status == DocumentStatus.FAILED
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_warning_only_sets_warning(self, service, doc_repo, storage, checker_engine):
        doc = _make_document()
        doc_repo.get_by_id = AsyncMock(return_value=doc)
        storage.download_file = Mock(return_value=_async_iter([b"pdf"]))
        checker_engine.run_checks = AsyncMock(
            return_value=(
                [
                    CheckOutput(
                        rule_code="vkr.fmt.spacing",
                        rule_name="Spacing",
                        severity=Severity.WARNING,
                        results=[RuleResult(status=CheckStatus.FAILED, message="Bad spacing")],
                    ),
                ],
                10,
            )
        )

        await service.run_checks_for_document(doc.id)

        assert doc.status == DocumentStatus.WARNING

    @pytest.mark.asyncio
    async def test_sets_checking_status_first(self, service, doc_repo, storage, checker_engine):
        doc = _make_document()
        doc_repo.get_by_id = AsyncMock(return_value=doc)
        storage.download_file = Mock(return_value=_async_iter([b"pdf"]))
        checker_engine.run_checks = AsyncMock(return_value=([], 0))

        statuses_seen: list[DocumentStatus] = []
        original_update = doc_repo.update

        async def capture_update(d):
            statuses_seen.append(d.status)
            return await original_update(d)

        doc_repo.update = AsyncMock(side_effect=capture_update)

        await service.run_checks_for_document(doc.id)

        assert statuses_seen[0] == DocumentStatus.CHECKING

    @pytest.mark.asyncio
    async def test_multiple_chunks_concatenated(self, service, doc_repo, storage, checker_engine):
        doc = _make_document()
        doc_repo.get_by_id = AsyncMock(return_value=doc)
        storage.download_file = Mock(return_value=_async_iter([b"chunk1", b"chunk2"]))
        checker_engine.run_checks = AsyncMock(return_value=([], 0))

        await service.run_checks_for_document(doc.id)

        call_args = checker_engine.run_checks.call_args
        assert call_args[0][0] == b"chunk1chunk2"


class TestGetResultsForDocument:
    @pytest.mark.asyncio
    async def test_delegates_to_repo(self, service, check_result_repo):
        doc_id = DocumentId(uuid.uuid4())
        expected = [
            CheckResult(
                id=CheckResultId(uuid.uuid4()),
                document_id=doc_id,
                rule_code="vkr.fmt",
                severity=Severity.ERROR,
                status=CheckStatus.PASSED,
                message="OK",
                details=None,
                created_at=datetime.now(UTC),
            )
        ]
        check_result_repo.list_for_document.return_value = expected

        result = await service.get_results_for_document(doc_id)

        check_result_repo.list_for_document.assert_awaited_once_with(doc_id)
        assert result == expected
