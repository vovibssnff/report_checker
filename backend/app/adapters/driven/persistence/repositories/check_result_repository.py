from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from app.adapters.driven.persistence.database.models.check_result import CheckResultModel
from app.core.domain.entities.check_result import CheckResult
from app.core.domain.value_objects import CheckResultId, CheckStatus, DocumentId, Severity
from app.core.ports.driven.check_result_repository import CheckResultRepository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession


class PgCheckResultRepository(CheckResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_document(
        self,
        document_id: DocumentId,
        results: Iterable[CheckResult],
    ) -> list[CheckResult]:
        await self._session.execute(delete(CheckResultModel).where(CheckResultModel.document_id == document_id))
        models = [self._entity_to_model(r) for r in results]
        self._session.add_all(models)
        await self._session.flush()
        return [self._model_to_entity(m) for m in models]

    async def list_for_document(self, document_id: DocumentId) -> list[CheckResult]:
        stmt = select(CheckResultModel).where(CheckResultModel.document_id == document_id)
        result = await self._session.execute(stmt)
        return [self._model_to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, result_id: CheckResultId) -> CheckResult:
        model = await self._session.get(CheckResultModel, result_id)
        if model is None:
            raise ValueError(f"CheckResult {result_id} not found")
        return self._model_to_entity(model)

    @staticmethod
    def _entity_to_model(entity: CheckResult) -> CheckResultModel:
        return CheckResultModel(
            id=entity.id,
            document_id=entity.document_id,
            rule_code=entity.rule_code,
            severity=entity.severity.value,
            status=entity.status.value,
            message=entity.message,
            details=entity.details,
            created_at=entity.created_at,
        )

    @staticmethod
    def _model_to_entity(model: CheckResultModel) -> CheckResult:
        return CheckResult(
            id=CheckResultId(model.id),
            document_id=DocumentId(model.document_id),
            rule_code=model.rule_code,
            severity=Severity(model.severity),
            status=CheckStatus(model.status),
            message=model.message,
            details=model.details,
            created_at=model.created_at,
        )
