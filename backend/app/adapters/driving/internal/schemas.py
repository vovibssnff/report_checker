from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.adapters.driving.web.schemas.document import CheckResultResponse


class InternalDocumentResponse(BaseModel):
    document_id: UUID
    status: str
    check_results: list[CheckResultResponse]
