from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.domain.value_objects import DocumentId
    from app.core.ports.driven.check_result_repository import CheckResultRepository
    from app.core.ports.driven.document_repository import DocumentRepository


class ReportExportService:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        check_result_repo: CheckResultRepository,
    ) -> None:
        self._doc_repo = doc_repo
        self._check_result_repo = check_result_repo

    async def export_csv(self, document_id: DocumentId) -> str:
        doc = await self._doc_repo.get_by_id(document_id)
        results = await self._check_result_repo.list_for_document(document_id)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["document", "rule_code", "severity", "status", "message"])
        for r in results:
            writer.writerow([doc.filename, r.rule_code, r.severity, r.status, r.message])
        return buf.getvalue()

    async def export_pdf_report(self, document_id: DocumentId) -> bytes:
        # TODO: replace with proper PDF generation (e.g. reportlab)
        csv_content = await self.export_csv(document_id)
        return csv_content.encode("utf-8")
