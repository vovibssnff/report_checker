from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.checkers.pdf_parser import parse_pdf

if TYPE_CHECKING:
    from app.checkers.base import BaseRule, RuleResult
    from app.checkers.registry import RuleRegistry
    from app.core.domain.value_objects import DocumentType, Severity
    from app.core.ports.driven.check_rule_repository import CheckRuleRepository


@dataclass
class CheckOutput:
    rule_code: str
    rule_name: str
    severity: Severity
    results: list[RuleResult] = field(default_factory=list)


class CheckerEngine:
    def __init__(self, registry: RuleRegistry, rule_repo: CheckRuleRepository) -> None:
        self._registry = registry
        self._rule_repo = rule_repo

    async def run_checks(self, pdf_bytes: bytes, doc_type: DocumentType) -> list[CheckOutput]:
        parsed = parse_pdf(pdf_bytes)

        db_rules = await self._rule_repo.list(document_type=doc_type, enabled=True)
        enabled_codes = {r.code for r in db_rules}
        config_overrides = {r.code: r.config for r in db_rules if r.config}

        rules = self._registry.get_rules(doc_type, enabled_codes=enabled_codes)
        if not rules:
            return []

        async def _run_one(rule: BaseRule) -> CheckOutput:
            config = config_overrides.get(rule.code, rule.default_config)
            results = await rule.check(parsed, config)
            return CheckOutput(
                rule_code=rule.code,
                rule_name=rule.name,
                severity=rule.default_severity,
                results=results,
            )

        outputs = await asyncio.gather(*[_run_one(r) for r in rules])
        return list(outputs)
