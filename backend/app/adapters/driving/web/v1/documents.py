from __future__ import annotations

import math
from time import perf_counter
from typing import TYPE_CHECKING
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.adapters.driven.observability import get_logger, kv
from app.adapters.driving.web.dependencies import (
    get_check_service,
    get_current_user,
    get_query_service,
    get_upload_service,
    get_user_repo,
)
from app.adapters.driving.web.schemas.common import PaginatedResponse
from app.adapters.driving.web.schemas.document import (
    CheckResultResponse,
    DocumentDetailResponse,
    DocumentResponse,
)
from app.core.domain.value_objects import DocumentId, DocumentStatus, DocumentType, Pagination
from app.core.domain.value_objects import UserRole

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driven.user_repository import UserRepository
    from app.core.ports.driving.document_checking import DocumentCheckUseCase
    from app.core.ports.driving.document_querying import DocumentQueryUseCase
    from app.core.ports.driving.document_uploading import DocumentUploadUseCase

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)


def _content_disposition_attachment(filename: str) -> str:
    """RFC 5987: ASCII fallback + filename*=UTF-8'' for non-ASCII."""
    try:
        filename.encode("ascii")
        value = f'attachment; filename="{filename}"'
    except UnicodeEncodeError:
        value = f"attachment; filename=document; filename*=UTF-8''{quote(filename, safe='')}"
    return value


def _can_access_document(user: User, owner_id) -> bool:
    if user.role in (UserRole.ADMIN, UserRole.TEACHER):
        return True
    if owner_id is None:
        return False
    return owner_id == user.id


@router.post("/", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile],
    document_type: str = Form(...),
    user: User = Depends(get_current_user),
    upload_service: DocumentUploadUseCase = Depends(get_upload_service),
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    query_service: DocumentQueryUseCase = Depends(get_query_service),
) -> list[DocumentResponse]:
    started = perf_counter()
    logger.info(
        "document_upload_requested %s",
        kv(user_id=user.id, files_count=len(files), document_type=document_type),
    )
    file_tuples = [(f.filename or "unknown", await f.read()) for f in files]
    docs = await upload_service.upload_for_user(user.id, DocumentType(document_type), file_tuples)
    logger.info(
        "document_upload_completed %s",
        kv(user_id=user.id, uploaded_count=len(docs), document_type=document_type),
    )

    responses: list[DocumentResponse] = []
    for doc in docs:
        check_started = perf_counter()
        logger.info("document_check_started %s", kv(document_id=doc.id, user_id=user.id))
        await check_service.run_checks_for_document(doc.id)
        check_elapsed_ms = round((perf_counter() - check_started) * 1000, 2)
        updated = await query_service.get_by_id(doc.id)
        logger.info(
            "document_check_completed %s",
            kv(document_id=doc.id, user_id=user.id, status=updated.status, duration_ms=check_elapsed_ms),
        )
        responses.append(DocumentResponse.model_validate(updated, from_attributes=True))
    total_elapsed_ms = round((perf_counter() - started) * 1000, 2)
    logger.info("document_upload_flow_completed %s", kv(user_id=user.id, duration_ms=total_elapsed_ms))
    return responses


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    document_type: str | None = Query(None),
    document_status: str | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    query_service: DocumentQueryUseCase = Depends(get_query_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> PaginatedResponse[DocumentResponse]:
    parsed_document_type = DocumentType(document_type) if document_type else None
    parsed_status = DocumentStatus(document_status) if document_status else None
    pagination = Pagination(page=page, size=size)
    if user.role in (UserRole.TEACHER, UserRole.ADMIN):
        docs, total = await query_service.list_all(
            document_type=parsed_document_type,
            status=parsed_status,
            pagination=pagination,
        )
    else:
        docs, total = await query_service.list_for_user(
            user.id,
            document_type=parsed_document_type,
            status=parsed_status,
            pagination=pagination,
        )
    uploader_names: dict = {}
    if user.role in (UserRole.TEACHER, UserRole.ADMIN):
        for doc in docs:
            if doc.user_id is None or doc.user_id in uploader_names:
                continue
            try:
                uploader = await user_repo.get_by_id(doc.user_id)
                uploader_names[doc.user_id] = uploader.name
            except ValueError:
                uploader_names[doc.user_id] = None
    return PaginatedResponse(
        items=[
            DocumentResponse.model_validate(d, from_attributes=True).model_copy(
                update={"uploader_name": uploader_names.get(d.user_id)}
            )
            for d in docs
        ],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if size else 0,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    query_service: DocumentQueryUseCase = Depends(get_query_service),
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    _user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    try:
        doc = await query_service.get_by_id(DocumentId(document_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from None
    if not _can_access_document(_user, doc.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    results = await check_service.get_results_for_document(DocumentId(document_id))
    return DocumentDetailResponse(
        **DocumentResponse.model_validate(doc, from_attributes=True).model_dump(),
        check_results=[CheckResultResponse.model_validate(r, from_attributes=True) for r in results],
    )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    query_service: DocumentQueryUseCase = Depends(get_query_service),
    _user: User = Depends(get_current_user),
) -> StreamingResponse:
    try:
        doc = await query_service.get_by_id(DocumentId(document_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from None
    if not _can_access_document(_user, doc.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    stream = await query_service.get_file_bytes(DocumentId(document_id))
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(doc.filename)},
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    query_service: DocumentQueryUseCase = Depends(get_query_service),
    _user: User = Depends(get_current_user),
) -> None:
    try:
        doc = await query_service.get_by_id(DocumentId(document_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from None
    if _user.role == UserRole.TEACHER and doc.user_id != _user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if _user.role == UserRole.STUDENT and doc.user_id != _user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await query_service.delete_document(DocumentId(document_id))


@router.get("/{document_id}/report")
async def export_report(
    document_id: UUID,
    format: str = Query("csv"),
    query_service: DocumentQueryUseCase = Depends(get_query_service),
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    _user: User = Depends(get_current_user),
) -> StreamingResponse:
    try:
        doc = await query_service.get_by_id(DocumentId(document_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from None
    if not _can_access_document(_user, doc.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    results = await check_service.get_results_for_document(DocumentId(document_id))

    if format == "csv":
        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["rule_code", "severity", "status", "message"])
        for r in results:
            writer.writerow([r.rule_code, r.severity, r.status, r.message])
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": _content_disposition_attachment(f"{doc.filename}_report.csv")},
        )

    async def _empty():
        yield b""

    return StreamingResponse(
        _empty(),
        media_type="application/pdf",
        headers={"Content-Disposition": _content_disposition_attachment(f"{doc.filename}_report.pdf")},
    )
