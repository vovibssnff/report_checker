from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, Form, UploadFile

from app.adapters.driving.internal.schemas import InternalDocumentResponse
from app.adapters.driving.web.dependencies import (
    get_check_service,
    get_query_service,
    get_upload_service,
)
from app.adapters.driving.web.schemas.document import CheckResultResponse
from app.core.domain.value_objects import DocumentId, DocumentType

if TYPE_CHECKING:
    from app.core.ports.driving.document_checking import DocumentCheckUseCase
    from app.core.ports.driving.document_querying import DocumentQueryUseCase
    from app.core.ports.driving.document_uploading import DocumentUploadUseCase

router = APIRouter(tags=["internal"])


@router.post("/documents/", response_model=list[InternalDocumentResponse])
async def upload_and_check(
    files: list[UploadFile],
    document_type: str = Form(...),
    source: str = Form("internal"),
    callback_url: str | None = Form(None),
    upload_service: DocumentUploadUseCase = Depends(get_upload_service),
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    query_service: DocumentQueryUseCase = Depends(get_query_service),
) -> list[InternalDocumentResponse]:
    file_tuples = [(f.filename or "unknown", await f.read()) for f in files]
    docs = await upload_service.upload_internal(DocumentType(document_type), file_tuples, source)
    responses: list[InternalDocumentResponse] = []
    for doc in docs:
        await check_service.run_checks_for_document(DocumentId(doc.id))
        doc = await query_service.get_by_id(DocumentId(doc.id))
        results = await check_service.get_results_for_document(DocumentId(doc.id))
        responses.append(
            InternalDocumentResponse(
                document_id=doc.id,
                status=doc.status,
                check_results=[CheckResultResponse.model_validate(r, from_attributes=True) for r in results],
            )
        )
    return responses


@router.get(
    "/documents/{document_id}/checks",
    response_model=list[CheckResultResponse],
)
async def get_check_results(
    document_id: UUID,
    check_service: DocumentCheckUseCase = Depends(get_check_service),
) -> list[CheckResultResponse]:
    results = await check_service.get_results_for_document(DocumentId(document_id))
    return [CheckResultResponse.model_validate(r, from_attributes=True) for r in results]
