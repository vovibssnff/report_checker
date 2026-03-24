from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING

from app.adapters.driven.observability import get_logger, kv
from app.checkers.pdf_parser import parse_pdf
from app.core.domain.value_objects import CheckStatus

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
        self._logger = get_logger(__name__)

    async def run_checks(self, pdf_bytes: bytes, doc_type: DocumentType) -> list[CheckOutput]:
        started = perf_counter()
        parsed = parse_pdf(pdf_bytes)

        db_rules = await self._rule_repo.list(document_type=doc_type, enabled=True)
        enabled_codes = {r.code for r in db_rules}
        config_overrides = {r.code: r.config for r in db_rules if r.config}
        self._logger.info(
            "checker_rules_loaded %s",
            kv(document_type=doc_type, enabled_db_rules=len(db_rules)),
        )

        rules = self._registry.get_rules(doc_type, enabled_codes=enabled_codes)
        if not rules:
            self._logger.warning("checker_rules_empty %s", kv(document_type=doc_type))
            return []
        self._logger.info(
            "checker_rules_selected %s",
            kv(document_type=doc_type, selected_codes=",".join(sorted(r.code for r in rules))),
        )

        async def _run_one(rule: BaseRule) -> CheckOutput:
            config = config_overrides.get(rule.code, rule.default_config)
            rule_started = perf_counter()
            self._logger.info("rule_check_started %s", kv(rule_code=rule.code, rule_name=rule.name))
            try:
                results = await rule.check(parsed, config)
            except Exception as err:
                elapsed_ms = round((perf_counter() - rule_started) * 1000, 2)
                self._logger.exception(
                    "rule_check_failed %s",
                    kv(rule_code=rule.code, rule_name=rule.name, duration_ms=elapsed_ms, error_type=type(err).__name__),
                )
                from app.checkers.base import RuleResult

                results = [
                    RuleResult(
                        status=CheckStatus.FAILED,
                        message=f"Rule execution error: {type(err).__name__}",
                        details={"rule_code": rule.code},
                    )
                ]
            elapsed_ms = round((perf_counter() - rule_started) * 1000, 2)
            failed_count = sum(1 for result in results if result.status == CheckStatus.FAILED)
            self._logger.info(
                "rule_check_completed %s",
                kv(
                    rule_code=rule.code,
                    rule_name=rule.name,
                    results_count=len(results),
                    failed_count=failed_count,
                    duration_ms=elapsed_ms,
                ),
            )
            return CheckOutput(
                rule_code=rule.code,
                rule_name=rule.name,
                severity=rule.default_severity,
                results=results,
            )

        outputs = await asyncio.gather(*[_run_one(r) for r in rules])
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        self._logger.info(
            "checker_run_completed %s",
            kv(document_type=doc_type, executed_rules=len(outputs), duration_ms=elapsed_ms),
        )
        return list(outputs)
