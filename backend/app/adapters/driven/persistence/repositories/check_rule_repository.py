from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.adapters.driven.persistence.database.models.check_rule import CheckRuleModel
from app.core.domain.entities.check_rule import CheckRule
from app.core.domain.value_objects import CheckRuleId, DocumentType
from app.core.ports.driven.check_rule_repository import CheckRuleRepository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.checkers.registry import RuleRegistry as RuleRegistryType


class PgCheckRuleRepository(CheckRuleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sync_from_registry(self, registry: RuleRegistryType) -> None:
        """Upsert rows for every code-defined rule so checks have DB-backed toggles/config.

        New rules are inserted enabled. Existing rows keep ``enabled`` and ``config``.
        """
        rules = registry.all_rules()
        if not rules:
            return
        values = [
            {
                "id": uuid.uuid4(),
                "code": r.code,
                "document_type": r.document_type.value,
                "name": r.name,
                "description": r.description or "",
                "enabled": True,
                "config": None,
            }
            for r in rules
        ]
        stmt = insert(CheckRuleModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[CheckRuleModel.code],
            set_={
                "document_type": stmt.excluded.document_type,
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "enabled": CheckRuleModel.enabled,
                "config": CheckRuleModel.config,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def list(
        self,
        *,
        document_type: DocumentType | None = None,
        enabled: bool | None = None,
    ) -> list[CheckRule]:
        stmt = select(CheckRuleModel)
        if document_type is not None:
            stmt = stmt.where(CheckRuleModel.document_type == document_type.value)
        if enabled is not None:
            stmt = stmt.where(CheckRuleModel.enabled == enabled)
        result = await self._session.execute(stmt)
        return [self._model_to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, rule_id: CheckRuleId) -> CheckRule:
        model = await self._session.get(CheckRuleModel, rule_id)
        if model is None:
            raise ValueError(f"CheckRule {rule_id} not found")
        return self._model_to_entity(model)

    async def upsert_many(self, rules: Iterable[CheckRule]) -> None:
        values = [
            {
                "id": r.id,
                "code": r.code,
                "document_type": r.document_type.value,
                "name": r.name,
                "description": r.description,
                "enabled": r.enabled,
                "config": r.config,
            }
            for r in rules
        ]
        if not values:
            return
        stmt = insert(CheckRuleModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["code"],
            set_={
                "document_type": stmt.excluded.document_type,
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "enabled": stmt.excluded.enabled,
                "config": stmt.excluded.config,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def update(self, rule: CheckRule) -> CheckRule:
        model = await self._session.get(CheckRuleModel, rule.id)
        if model is None:
            raise ValueError(f"CheckRule {rule.id} not found")
        model.code = rule.code
        model.document_type = rule.document_type.value
        model.name = rule.name
        model.description = rule.description
        model.enabled = rule.enabled
        model.config = rule.config
        await self._session.flush()
        return self._model_to_entity(model)

    @staticmethod
    def _entity_to_model(entity: CheckRule) -> CheckRuleModel:
        return CheckRuleModel(
            id=entity.id,
            code=entity.code,
            document_type=entity.document_type.value,
            name=entity.name,
            description=entity.description,
            enabled=entity.enabled,
            config=entity.config,
        )

    @staticmethod
    def _model_to_entity(model: CheckRuleModel) -> CheckRule:
        return CheckRule(
            id=CheckRuleId(model.id),
            code=model.code,
            document_type=DocumentType(model.document_type),
            name=model.name,
            description=model.description,
            enabled=model.enabled,
            config=model.config,
        )
