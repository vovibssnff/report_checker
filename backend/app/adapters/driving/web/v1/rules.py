from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.adapters.driving.web.dependencies import get_rule_service, require_admin
from app.adapters.driving.web.schemas.rule import RuleResponse, RuleUpdateRequest
from app.core.domain.value_objects import CheckRuleId, DocumentType

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driving.rule_managing import RuleManagementUseCase

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=list[RuleResponse])
async def list_rules(
    document_type: str | None = Query(None),
    enabled: bool | None = Query(None),
    rule_service: RuleManagementUseCase = Depends(get_rule_service),
) -> list[RuleResponse]:
    rules = await rule_service.list_rules(
        document_type=DocumentType(document_type) if document_type else None,
        enabled=enabled,
    )
    return [RuleResponse.model_validate(r, from_attributes=True) for r in rules]


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    body: RuleUpdateRequest,
    rule_service: RuleManagementUseCase = Depends(get_rule_service),
    _admin: User = Depends(require_admin),
) -> RuleResponse:
    rule = await rule_service.update_rule(
        CheckRuleId(rule_id),
        enabled=body.enabled,
        config=body.config,
    )
    return RuleResponse.model_validate(rule, from_attributes=True)
