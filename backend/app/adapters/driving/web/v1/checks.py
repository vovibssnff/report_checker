from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.adapters.driving.web.dependencies import get_check_service, get_current_user
from app.adapters.driving.web.schemas.document import CheckResultResponse
from app.core.domain.value_objects import DocumentId

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driving.document_checking import DocumentCheckUseCase

router = APIRouter(tags=["checks"])


@router.post(
    "/documents/{document_id}/checks",
    response_model=list[CheckResultResponse],
    status_code=status.HTTP_201_CREATED,
)
async def run_checks(
    document_id: UUID,
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    _user: User = Depends(get_current_user),
) -> list[CheckResultResponse]:
    results = await check_service.run_checks_for_document(DocumentId(document_id))
    return [CheckResultResponse.model_validate(r, from_attributes=True) for r in results]


@router.get(
    "/documents/{document_id}/checks",
    response_model=list[CheckResultResponse],
)
async def get_check_results(
    document_id: UUID,
    check_service: DocumentCheckUseCase = Depends(get_check_service),
    _user: User = Depends(get_current_user),
) -> list[CheckResultResponse]:
    results = await check_service.get_results_for_document(DocumentId(document_id))
    return [CheckResultResponse.model_validate(r, from_attributes=True) for r in results]
