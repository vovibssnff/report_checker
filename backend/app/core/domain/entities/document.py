from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from app.core.domain.value_objects import DocumentId, DocumentStatus, DocumentType, UserId


@dataclass
class Document:
    id: DocumentId
    document_type: DocumentType
    filename: str
    s3_key: str
    file_size: int
    status: DocumentStatus
    source: str
    uploaded_at: datetime
    checked_at: datetime | None
    user_id: UserId | None
    page_count: int | None = None
