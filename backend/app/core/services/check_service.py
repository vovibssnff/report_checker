from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.core.domain.entities.check_result import CheckResult
from app.core.domain.value_objects import (
    CheckResultId,
    CheckStatus,
    DocumentId,
    DocumentStatus,
    Severity,
)
from app.core.ports.driving.document_checking import DocumentCheckUseCase

if TYPE_CHECKING:
    from app.checkers.engine import CheckerEngine
    from app.core.ports.driven.check_result_repository import CheckResultRepository
    from app.core.ports.driven.document_repository import DocumentRepository
    from app.core.ports.driven.file_storage import FileStoragePort


class CheckService(DocumentCheckUseCase):
    def __init__(
        self,
        doc_repo: DocumentRepository,
        check_result_repo: CheckResultRepository,
        storage: FileStoragePort,
        checker_engine: CheckerEngine,
    ) -> None:
        self._doc_repo = doc_repo
        self._check_result_repo = check_result_repo
        self._storage = storage
        self._checker_engine = checker_engine

    async def run_checks_for_document(self, document_id: DocumentId) -> list[CheckResult]:
        doc = await self._doc_repo.get_by_id(document_id)
        doc.status = DocumentStatus.CHECKING
        await self._doc_repo.update(doc)

        chunks: list[bytes] = []
        stream = self._storage.download_file(doc.s3_key)
        async for chunk in stream:
            chunks.append(chunk)
        pdf_bytes = b"".join(chunks)

        outputs = await self._checker_engine.run_checks(pdf_bytes, doc.document_type)

        now = datetime.now(UTC)
        results: list[CheckResult] = []
        for output in outputs:
            for rr in output.results:
                results.append(
                    CheckResult(
                        id=CheckResultId(uuid.uuid4()),
                        document_id=document_id,
                        rule_code=output.rule_code,
                        severity=output.severity,
                        status=rr.status,
                        message=rr.message,
                        details=rr.details,
                        created_at=now,
                    )
                )

        saved = await self._check_result_repo.replace_for_document(document_id, results)

        has_error = any(r.status == CheckStatus.FAILED and r.severity == Severity.ERROR for r in saved)
        has_warning = any(r.status == CheckStatus.FAILED and r.severity == Severity.WARNING for r in saved)

        if has_error:
            doc.status = DocumentStatus.FAILED
        elif has_warning:
            doc.status = DocumentStatus.WARNING
        else:
            doc.status = DocumentStatus.PASSED

        doc.checked_at = now
        await self._doc_repo.update(doc)

        return saved

    async def get_results_for_document(self, document_id: DocumentId) -> list[CheckResult]:
        return await self._check_result_repo.list_for_document(document_id)
